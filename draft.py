#!/usr/bin/python

import dweepy
import uuid
import time
import collections
import threading

class DweepyThreadListener(object):
    def __init__(self, thing, callback):

        def listen(thing, callback):
            print('Start listening on ' + thing)
            for dweet in dweepy.listen_for_dweets_from(thing):
                callback(dweet)

        self.thread = threading.Thread(target=listen, args = (thing,callback,))
        self.thread.start()

class Sensor(object):
    def __init__(self, discovery_thing):
        self.ctrl_data_lock = threading.Lock()
        self.ctrl_data = collections.deque(maxlen = 1000)
        self.discovery_thing = discovery_thing
        self.uuid_rt_data = discovery_thing + '.' + str(uuid.uuid1()) + '.rt_data'
        self.uuid_ctrl = discovery_thing + '.' + str(uuid.uuid1()) + '.ctrl'
        self.listeners = []

        print('Registered sensor data stream on: ' + self.uuid_rt_data)
        print('Registered sensor control on: ' + self.uuid_ctrl)
        print('Advertising sensor presence on: ' + self.discovery_thing)

        dweepy.dweet_for(self.discovery_thing,
        {
            'method'    : 'advertise',
            'type'      : 'sensor',
            'rt_data'   : self.uuid_rt_data,
            'ctrl'      : self.uuid_ctrl
        })

        self.listeners.append(DweepyThreadListener(self.discovery_thing, self._lookup_callback))
        self.listeners.append(DweepyThreadListener(self.uuid_ctrl, self._ctrl_callback))

    def _lookup_callback(self, data):
        print(data)

    def _ctrl_callback(self, data):
        with self.ctrl_data_lock:
            print(data)

    def send_data(self, data):
        dweepy.dweet_for(self.uuid_rt_data, data)

    def get_ctrl_data(self):
        with self.ctrl_data_lock():
            return self.ctrl_data.popleft()

class DweetExchange(object):
    def __init__(self, type, discovery_thing):
        if type == 'sensor':
            self.delegate = Sensor(discovery_thing)

    def send_data(self, data):
        self.delegate.send_data(data)

    def get_ctrl(self, data):
        self.delegate.get_ctrl(data)

discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
exch = DweetExchange('sensor', discovery)
var = 1

while True:
    print('sending')
    var = var + 1
    exch.send_data({'hello' : var})
    time.sleep(1)  # Delay for 1 minute (60 seconds)
