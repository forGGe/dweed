#!/usr/bin/python

import dweed
import sys
import time
import bokeh

def do_sensor():
    discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
    dweed._discovery_add_service(discovery, 'test_discovery')
    sensor = dweed.DweetExchange.get_thing('sensor', 'test_sensor', discovery)
    var = 1

    while True:
        data = {'moisture' : var, 'ts' : time.time()}
        print('Sending ' + str(data))
        var = var + 1
        sensor.send_data(data)

        ctrl = sensor.get_ctrl_data()

        if ctrl:
            print('Received ' + str(ctrl))

        time.sleep(1)

def do_view():
    discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
    dweed._discovery_add_service(discovery, 'test_discovery')
    view = dweed.DweetExchange.get_thing('view', 'test_view', discovery)

    while True:
        sensors = view.lookup_sensors()

        if sensors:
            print(sensors)

            # Get some data
            gen = view.listen_for_sensor_data(sensors[0])
            for data in gen:
                print(data)

if sys.argv[1] == 'view':
    do_view()
elif sys.argv[1] == 'sensor':
    do_sensor()
