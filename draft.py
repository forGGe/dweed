#!/usr/bin/python

import dweed
import sys
import time
import bokeh
import random

from threading import Thread

from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure
from bokeh.driving import linear
from bokeh.client import push_session

from tornado import gen

def do_sensor():
    discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
    dweed._discovery_add_service(discovery, 'test_discovery')
    sensor = dweed.DweetExchange.get_thing('sensor', 'test_sensor', discovery)

    while True:
        data = {'moisture' : random.randint(0,100), 'ts' : time.time()}
        print('Sending ' + str(data))
        sensor.send_data(data)

        ctrl = sensor.get_ctrl_data()

        if ctrl:
            print('Received ' + str(ctrl))

        time.sleep(1)


def do_view():
    p = figure(plot_width=400, plot_height=400)
    r = p.line([], [], color="firebrick", line_width=2)
    ds = r.data_source
    # curdoc().add_root(p)

    # open a session to keep our local document in sync with server
    session = push_session(curdoc())

    def update_plot():
        # print('> Update! ')
        # ds.data['x'].append(random.randint(0,100))
        # ds.data['y'].append(random.randint(0,100))
        ds.trigger('data', ds.data, ds.data)

    def do_discovery():
        discovery = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
        dweed._discovery_add_service(discovery, 'test_discovery')
        view = dweed.DweetExchange.get_thing('view', 'test_view', discovery)

        while True:
            sensors = view.lookup_sensors()

            if sensors:
                print(sensors)

                # Get some data
                for data in view.listen_for_sensor_data(sensors[0]):
                    print(data)
                    ds.data['x'].append(data['ts'])
                    ds.data['y'].append(data['moisture'])

    curdoc().add_periodic_callback(update_plot, 1000)

    thread = Thread(target=do_discovery)
    thread.start()

    session.show(p) # open the document in a browser
    session.loop_until_closed() # run forever

if sys.argv[1] == 'view':
    do_view()
elif sys.argv[1] == 'sensor':
    do_sensor()
