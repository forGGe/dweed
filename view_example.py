import dweed
import sys
import time
import bokeh
import random

from threading import Thread

from tornado.ioloop import IOLoop

from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.models import ColumnDataSource
from bokeh.server.server import Server, BokehTornado

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

        io_loop.add_callback(server.show, '/')
        io_loop.start()

def do_discovery():
    # Discovery id is supplied by user
    discovery_id = sys.argv[1]

    # Advertise view via given dicsovery
    discovery = dweed.Discovery(discovery_id, 'test_discovery')
    view = dweed.DweetExchange.get_thing('view', 'test_view', discovery)

    while True:
        # Find some sensors
        sensors = view.lookup_sensors()

        # Sensors found
        if sensors:
            print(sensors)

            try:
                # Get some sensor data
                for data in view.listen_for_sensor_data(sensors[0]):
                    print(data)

                    # Pass data to plotter
                    p.add_point(data['ts'], data['moisture'])
            except Exception as e:
                print("Restarting lookup: " + str(e))
                pass

# Create plotter
p = Plotter()

# Do the dweed work in separate thread
thread = Thread(target=do_discovery)
thread.start()

# Start plotting
p.start()
