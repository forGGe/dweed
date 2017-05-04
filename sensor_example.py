#!/usr/bin/python

import dweed
import sys
import time
import random

# Discovery id is supplied by user
discovery_id = sys.argv[1]

print('Starting sensor dweed example using discovery ID: ' + discovery_id)

# Advertise sensor via given dicsovery
discovery = dweed.Discovery(discovery_id, 'test_discovery')
sensor = dweed.DweetExchange.get_thing('sensor', 'test_sensor', discovery)

while True:
    # Start sending data
    data = {'moisture' : random.randint(0,100), 'ts' : time.time()}
    print('Sending ' + str(data))
    sensor.send_data(data)

    # Check if anyone has send some control data to sensor
    ctrl = sensor.get_ctrl_data()

    if ctrl:
        print('Received ' + str(ctrl))

    time.sleep(1)
