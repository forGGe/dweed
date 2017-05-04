#!/usr/bin/python

import dweepy
import uuid
import time
import collections
import threading
import random
import sys

class DweepyThreadListener(object):
    def __init__(self, thing, callback, timeout=32):

        def listen_dweets(thing, callback):
            while 1:
                try:
                    print('Start listening on ' + thing)
                    for dweet in dweepy.listen_for_dweets_from(thing, timeout):
                        callback(dweet)

                except Exception as e:
                    print('Restarting listen due to exception: ' + str(e))
                    time.sleep(1)
                    pass

        self.thread = threading.Thread(target=listen_dweets, args = (thing,callback,))
        self.thread.start()

_discovery_things = {}

class Discovery(object):
    def __init__(self, discovery_thing, name = ''):
        self.discovery_thing = discovery_thing
        self.name = name
        self.listener = DweepyThreadListener(discovery_thing, self._discovery_cb)
        self.things = []

        print('Registering new discovery service \'' + name + '\' on ' + discovery_thing)

    def add_thing(self, thing, type, name, adv_data):
        print('Adding \'' + name  + '\' on ' + thing + ' to the discovery service ' + self.discovery_thing)
        self.things.append({
            'name' : name,
            'self' : thing,
            'type' : type,
            'adv_data' : adv_data,
            'lookups' : [] # List of desired things to lookup for
        })

    def start_lookup(self, thing, type, name, callback):
        for reg_thing in self.things:
            if reg_thing['self'] == thing:
                reg_thing['lookups'].append({
                    'type'          : type,
                    'name'          : name,
                    'cb'            : callback
                })

        while 1:
            try:
                print('Lookup for ' + type + ' on ' + self.discovery_thing)
                dweepy.dweet_for(self.discovery_thing, {
                    'method'    : 'lookup',
                    'type'      : type,
                    'self'      : thing,
                    'name'      : name,
                    'ts'        : time.time()
                })

                return
            except Exception as e:
                delay = random.randint(2, 10)
                print('Restarting lookup in ' + str(delay) + ' seconds due to error: ' + str(e))
                time.sleep(random.randint(2, 10))

    def stop_lookup(self, thing, type):
        for reg_thing in self.things:
            if reg_thing == thing:
                reg_thing['lookups'] = [it for it in reg_thing['lookups'] if reg_thing['lookups']['type'] != type]

    def _advertise(self, thing, type, name, adv_data):
        while 1:
            try:
                print('Advertising ' + type + ' on ' + thing + ' with data: ' + str(adv_data))
                dweepy.dweet_for(self.discovery_thing, {
                    'method'    : 'advertise',
                    'type'      : type,
                    'self'      : thing,
                    'name'      : name,
                    'adv_data'  : adv_data,
                    'ts'        : time.time()
                })

                return
            except Exception as e:
                delay = random.randint(2, 10)
                print('Restarting advertise in ' + str(delay) + ' seconds due to error: ' + str(e))
                time.sleep(delay)

    def _discovery_cb(self, data):
        try:
            method = data['content']['method']
            type = data['content']['type']

            if method == 'lookup':
                print('Received lookup reqest for type: ' + type)

                for thing in self.things:
                    if thing['type'] == type:
                        self._advertise(thing['self'], type, thing['name'], thing['adv_data'])

            if method == 'advertise':
                print('Received advertise packet of: ' + type)

                for thing in self.things:
                    for desired in thing['lookups']:
                        if desired['type'] == type:
                            desired['cb'](data['content'])

        except Exception as e:
            print(e)
            print('Invalid data on the channel! ' + str(data))

################################################################################

class Sensor(object):
    def __init__(self, name, discovery):
        self.ctrl_data_lock = threading.Lock()
        self.ctrl_data = collections.deque(maxlen = 32)
        self.name = name
        self.discovery = discovery
        self.uuid = str(uuid.uuid1())
        self.uuid_rt_data = discovery.discovery_thing + '.' + self.uuid + '.rt_data'
        self.uuid_ctrl = discovery.discovery_thing + '.' + self.uuid + '.ctrl'
        self.listeners = []

        print('Registered sensor data stream on: ' + self.uuid_rt_data)
        print('Registered sensor control on: ' + self.uuid_ctrl)

        adv_data = { 'rt_data' : self.uuid_rt_data, 'ctrl' : self.uuid_ctrl }

        self.listeners.append(DweepyThreadListener(self.uuid_ctrl, self._ctrl_callback))
        self.discovery.add_thing(self.uuid, 'sensor', name, adv_data)

    def _ctrl_callback(self, data):
        with self.ctrl_data_lock:
            self.ctrl_data.append(data)

    def send_data(self, data):
        dweepy.dweet_for(self.uuid_rt_data, data)

    def get_ctrl_data(self):
        with self.ctrl_data_lock:
            try:
                return self.ctrl_data.popleft()
            except:
                return None

class View(object):
    def __init__(self, name, discovery):
        self.name = name
        self.discovery = discovery
        self.uuid = str(uuid.uuid1())

        print('Registered view on: ' + self.uuid)
        adv_data = { 'noop' : 'noop' }
        discovery.add_thing(self.uuid, 'view', name, adv_data)

    def lookup_sensors(self, name = '*', lookup_time = 10):
        sensors = []

        def lookup_cb(sensor_data):
            name = sensor_data['name']
            thing = sensor_data['self']
            adv_data = sensor_data['adv_data']

            sensors.append({ 'thing' : thing, 'name' : name, 'adv_data' : adv_data })

        self.discovery.start_lookup(self.uuid, 'sensor', name, lookup_cb)
        time.sleep(lookup_time)
        self.discovery.stop_lookup(self.uuid, 'sensor')

        return sensors

    def listen_for_sensor_data(self, sensor_data, stream_timeout=31557600):
        print('Listening for data from: ' + sensor_data['adv_data']['rt_data'])
        for data in dweepy.listen_for_dweets_from(sensor_data['adv_data']['rt_data'], stream_timeout):
            retval = data['content']
            yield retval

################################################################################

class DweetExchange(object):
    @staticmethod
    def get_thing(type, name, discovery_thing):
        if type == 'sensor':
            return Sensor(name, discovery_thing)
        if type == 'view':
            return View(name, discovery_thing)
