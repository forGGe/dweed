#!/usr/bin/python

import dweed
import sys
import time
import bokeh
import random

from threading import Thread

from tornado.ioloop import IOLoop

from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure
from bokeh.driving import linear
from bokeh.client import push_session
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.server.server import Server, BokehTornado

from tornado import gen

def do_sensor():
    discovery_uuid = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
    discovery = dweed.Discovery(discovery_uuid, 'test_discovery')
    sensor = dweed.DweetExchange.get_thing('sensor', 'test_sensor', discovery)

    while True:
        data = {'moisture' : random.randint(0,100), 'ts' : time.time()}
        print('Sending ' + str(data))
        sensor.send_data(data)

        ctrl = sensor.get_ctrl_data()

        if ctrl:
            print('Received ' + str(ctrl))

        time.sleep(1)

class Plotter:
    def __init__(self):
        self.i = 0
        self.data = []

    def add_point(self, x, y):
        self.data.append({ 'x' : x, 'y' : y})

    def start(self):
        def plotter(doc):
            # Base data
            x = [ item['x'] for item in self.data ]
            y = [ item['y'] for item in self.data ]

            ds = ColumnDataSource(data=dict(x=x, y=y))

            def update_plot():
                new = {}
                if len(self.data):
                    new = { 'x' : [ self.data[-1]['x'] ], 'y' : [ self.data[-1]['y'] ] }

                last = {}
                if len(ds.data['x']):
                    last = { 'x' : [ ds.data['x'][-1] ], 'y' : [ ds.data['y'][-1] ] }

                if new != last:
                    print('Displaying new data')
                    ds.stream(new)

            p = figure(plot_width=1200, plot_height=400)
            p.line('x', 'y', color="firebrick", line_width=2, source=ds)

            doc.add_periodic_callback(update_plot, 1000)

            doc.add_root(p)

        io_loop = IOLoop.current()
        bokeh_app = Application(FunctionHandler(plotter))
        server = Server({'/': bokeh_app}, io_loop=io_loop, host="*")

        server.start()

        print('Opening Bokeh application on http://localhost:5006/')

        io_loop.add_callback(server.run_until_shutdown)
        io_loop.start()


def do_view():
    p = Plotter()

    def do_discovery():
        discovery_uuid = 'd1e7a182-9f8a-440d-b9f8-13737b1e4f37'
        discovery = dweed.Discovery(discovery_uuid, 'test_discovery')
        view = dweed.DweetExchange.get_thing('view', 'test_view', discovery)

        while True:
            sensors = view.lookup_sensors()

            if sensors:
                print(sensors)

                # Get some data
                try:
                    for data in view.listen_for_sensor_data(sensors[0], 20):
                        print(data)
                        p.add_point(data['ts'], data['moisture'])
                except:
                    pass

    thread = Thread(target=do_discovery)
    thread.start()

    p.start()

if sys.argv[1] == 'view':
    do_view()
elif sys.argv[1] == 'sensor':
    do_sensor()
