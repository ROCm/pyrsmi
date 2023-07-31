# MIT License
# 
# Copyright (c) 2023 Advanced Micro Devices, Inc.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys

from bokeh.server.server import Server
from tornado.ioloop import IOLoop
from tornado import web

import apps


DEFAULT_PORT = 5006


routes = {
    '/CPU-Utilization': apps.cpu.cpu,
    '/CPU-Resources': apps.cpu.resource_timeline,
}

if apps.gpu.ngpus > 0:
    routes['/GPU-Utilization'] = apps.gpu.gpu
    routes['/GPU-Memory'] = apps.gpu.gpu_mem
    routes['/GPU-Resources'] = apps.gpu.gpu_resource_timeline
    routes['/System-Resources'] = apps.gpu.system_resource_timeline

class RouteIndex(web.RequestHandler):
    """ A JSON index of all routes present on the Bokeh Server """

    def get(self):
        self.write({route: route.strip("/").replace("-", " ") for route in routes})


def go():
    print(f'ngpus = {apps.gpu.ngpus}')
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = DEFAULT_PORT
    server = Server(routes, port=port, allow_websocket_origin=["*"])
    server.start()

    server._tornado.add_handlers(
        r".*", [(server.prefix + "/" + "index.json", RouteIndex, {})]
    )

    IOLoop.current().start()


if __name__ == "__main__":
    go()
