#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Application monitoring
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


import os
import time
import threading

from   PyQt5.QtCore import QObject, pyqtSignal
from   logger import logger as lg

PERIOD = 0.25

#-------------------------------------------------------------------------------
class AppMonitor(QObject):

    file_changed_signal = pyqtSignal( str )

    #-------------------------------------------------------    
    def __init__(self, fname):
        super().__init__()
        self.stamp = 0
        self.fname = fname

    #-------------------------------------------------------    
    def processing(self):
        stamp = os.stat(self.fname).st_mtime
        if stamp != self.stamp:
            self.stamp = stamp
            self.file_changed_signal.emit(self.fname)
        
#-------------------------------------------------------------------------------
class AppMonitorThread(threading.Thread):

    #-------------------------------------------------------
    def __init__(self, log_file, name='AppMon Thread' ):
        super().__init__()
        self._finish_event = threading.Event()
        self.monitor = AppMonitor(log_file)

    #-------------------------------------------------------
    def finish(self):
        self._finish_event.set()
        lg.info('Application Monitor Thread pending to finish')

    #-------------------------------------------------------
    def run(self):
        while True:
            time.sleep(PERIOD)
            self.watcher.processing()
            if self._finish_event.is_set():
                return
            
#-------------------------------------------------------------------------------
    
