#!/usr/bin/python

import dweepy
import uuid
import time
import collections
import threading

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

class Sensor(object):
    def __init__(self, discovery_thing):
        self.ctrl_data_lock = threading.Lock()
        self.ctrl_data = collections.deque(maxlen = 32)
        self.discovery_thing = discovery_thing
        self.uuid = str(uuid.uuid1())
        self.uuid_rt_data = discovery_thing + '.' + self.uuid + '.rt_data'
        self.uuid_ctrl = discovery_thing + '.' + self.uuid + '.ctrl'
        self.listeners = []

        print('Registered sensor data stream on: ' + self.uuid_rt_data)
        print('Registered sensor control on: ' + self.uuid_ctrl)

        self.listeners.append(DweepyThreadListener(self.discovery_thing, self._lookup_callback))
        self.listeners.append(DweepyThreadListener(self.uuid_ctrl, self._ctrl_callback))

        self._send_discovery()

    def _send_discovery(self):
        print('Advertising sensor presence on: ' + self.discovery_thing)
        dweepy.dweet_for(self.discovery_thing,
        {
            'method'    : 'advertise',
            'type'      : 'sensor',
            'self'      : self.uuid,
            'rt_data'   : self.uuid_rt_data,
            'ctrl'      : self.uuid_ctrl
        })

    def _lookup_callback(self, data):
        try:
            method = data['content']['method']
            type = data['content']['type']

            if method == 'lookup' and type == 'sensor':
                self._send_discovery()
            else:
                print('Discovery data received and ignored ' + str(data))
        except:
            print('Invalid data on the channel! ' + str(data))

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
    def __init__(self, type, discovery_thing):
        if type == 'sensor':
            self.delegate = Sensor(discovery_thing)

    def send_data(self, data):
        self.delegate.send_data(data)

    def get_ctrl_data(self):
        return self.delegate.get_ctrl_data()

discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
exch = DweetExchange('sensor', discovery)
var = 1

while True:
    data = {'hello' : var}
    print('Sending ' + str(data))
    var = var + 1
    exch.send_data(data)

    ctrl = exch.get_ctrl_data()

    if ctrl:
        print('Received ' + str(ctrl))

    time.sleep(1)
