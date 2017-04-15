#!/usr/bin/python

import dweepy
import uuid
import time
import collections
import threading
import random

class DweepyThreadListener(object):
    def __init__(self, thing, callback):

        def listen(thing, callback):
            while 1:
                try:
                    print('Start listening on ' + thing)
                    for dweet in dweepy.listen_for_dweets_from(thing, timeout=20):
                        callback(dweet)
                except:
                    print('Restarting listen due to exception')
                    time.sleep(2)
                    pass

        self.thread = threading.Thread(target=listen, args = (thing,callback,))
        self.thread.start()

_discovery_things = {}

def _discovery_advertise(discovery_thing, thing, type, name, adv_data):

    while 1:
        try:
            print('Advertising ' + type + ' on ' + thing + ' with data: ' + str(adv_data))
            dweepy.dweet_for(discovery_thing, {
                'method'    : 'advertise',
                'type'      : type,
                'self'      : thing,
                'adv_data'  : adv_data
            })

            return
        except Exception as e:
            delay = random.randint(2, 10)
            print('Restarting advertise in ' + str(delay) + ' seconds due to error: ' + str(e))
            time.sleep(random.randint(2, 10))

def _discovery_callback(data):
    try:
        method = data['content']['method']
        type = data['content']['type']
        discovery_thing = data['thing'] # Discovery thing that emitted message

        if not discovery_thing in _discovery_things:
            print('Unknown discovery thing: ' + discovery_thing + ' . Ignoring packet')
            return

        if method == 'lookup':
            print('Received lookup reqest for type: ' + type)
            things = _discovery_things[discovery_thing]['things']

            for thing in things:
                if thing['type'] == type:
                    _discovery_advertise(discovery_thing,
                            thing['self'], type,
                            thing['name'], thing['adv_data'])


        # if method == 'lookup' and type == 'sensor':
        #     self._send_discovery()
        # else:
        #     print('Discovery data received and ignored ' + str(data))
    except Exception as e:
        print(e)
        print('Invalid data on the channel! ' + str(data))

def _discovery_add_service(discovery_thing, name = ''):
    print('Registering new discovery service \'' + name + '\' on ' + discovery_thing)
    _discovery_things[discovery_thing] = {
        'name' : name,
        'listener' : DweepyThreadListener(discovery_thing, _discovery_callback),
        'things' : []
    }

def _discovery_add_thing(discovery_thing, thing, type, name, adv_data):
    print('Adding \'' + name  + '\' on ' + thing + ' to the discovery service ' + discovery_thing)
    _discovery_things[discovery_thing]['things'].append({
        'name' : name,
        'self' : thing,
        'type' : type,
        'adv_data' : adv_data
    })

class Sensor(object):
    def __init__(self, name, discovery_thing):
        self.ctrl_data_lock = threading.Lock()
        self.ctrl_data = collections.deque(maxlen = 32)
        self.name = name
        self.discovery_thing = discovery_thing
        self.uuid = str(uuid.uuid1())
        self.uuid_rt_data = discovery_thing + '.' + self.uuid + '.rt_data'
        self.uuid_ctrl = discovery_thing + '.' + self.uuid + '.ctrl'
        self.listeners = []

        print('Registered sensor data stream on: ' + self.uuid_rt_data)
        print('Registered sensor control on: ' + self.uuid_ctrl)

        adv_data = { 'rt_data' : self.uuid_rt_data, 'ctrl' : self.uuid_ctrl }

        # self.listeners.append(DweepyThreadListener(self.discovery_thing, self._lookup_callback))
        self.listeners.append(DweepyThreadListener(self.uuid_ctrl, self._ctrl_callback))
        _discovery_add_thing(discovery_thing, self.uuid, 'sensor', name, adv_data)

    # def _send_discovery(self):
    #     print('Advertising sensor presence on: ' + self.discovery_thing)
    #     dweepy.dweet_for(self.discovery_thing,
    #     {
    #         'method'    : 'advertise',
    #         'type'      : 'sensor',
    #         'self'      : self.uuid,
    #         'rt_data'   : self.uuid_rt_data,
    #         'ctrl'      : self.uuid_ctrl,
    #     })

    # def _lookup_callback(self, data):
    #     try:
    #         method = data['content']['method']
    #         type = data['content']['type']
    #
    #         if method == 'lookup' and type == 'sensor':
    #             self._send_discovery()
    #         else:
    #             print('Discovery data received and ignored ' + str(data))
    #     except:
    #         print('Invalid data on the channel! ' + str(data))

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

class DweetExchange(object):
    @staticmethod
    def get_thing(type, name, discovery_thing):
        if type == 'sensor':
            return Sensor(name, discovery_thing)

discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
_discovery_add_service(discovery, 'test_discovery')
sensor = DweetExchange.get_thing('sensor', 'test_sensor', discovery)
var = 1

while True:
    data = {'hello' : var}
    print('Sending ' + str(data))
    var = var + 1
    sensor.send_data(data)

    ctrl = sensor.get_ctrl_data()

    if ctrl:
        print('Received ' + str(ctrl))

    time.sleep(1)
