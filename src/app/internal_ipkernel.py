#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Internal IPython Kernel support
#
#    Copyright (c) 2016-2017, 2024, Camlab Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

import sys

#from IPython.lib.kernel  import connect_qtconsole
from ipykernel  import connect_qtconsole
from ipykernel.kernelapp import IPKernelApp

from logger   import logger as lg

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------
def mpl_kernel(gui):
    """Launch and return an IPython kernel with matplotlib support for the desired gui
    """
    kernel = IPKernelApp.instance(log=lg)
    try:
        kernel.initialize(['python', '--matplotlib=%s' % gui,
                           #'--log-level=10'
                          ])
    except Exception:
        sys.stdout = sys.__stdout__
        lg.warning('kernelApp.initialize failed!')
        raise
        
    return kernel


class InternalIPKernel(object):

    def init_ipkernel(self, backend, context):
        # Start IPython kernel with GUI event loop and mpl support
        self.ipkernel = mpl_kernel(backend)
        # To create and track active qt consoles
        self.consoles = []
        
        # This application will also act on the shell user namespace
        self.namespace = self.ipkernel.shell.user_ns

        for key in context.keys():
            self.namespace[key] = context[key]
        #self.namespace['ipkernel'] = self.ipkernel  # dbg

    def print_namespace(self, evt=None):
        print("\n***Variables in User namespace***")
        for k, v in self.namespace.items():
            if not k.startswith('_'):
                print('%s -> %r' % (k, v))
        sys.stdout.flush()

    def new_qt_console(self, evt=None):
        """start a new qtconsole connected to our kernel"""
        return connect_qtconsole(self.ipkernel.abs_connection_file, profile=self.ipkernel.profile)

    def count(self, evt=None):
        self.namespace['app_counter'] += 1

    def cleanup_consoles(self, evt=None):
        lg.warning('cleanup consoles')
        for c in self.consoles:
            c.kill()

