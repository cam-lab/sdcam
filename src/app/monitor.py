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

import numpy as np

from   PyQt5.QtCore import QObject, pyqtSignal
from   logger import logger as lg

PERIOD = 0.1

#-------------------------------------------------------------------------------
class FrameParam:

    def __init__(self, buf_len = 50):
        self.value       = 0
        self.mean        = 0
        self.min         = 1000
        self.max         = 0
        self.sdev        = 0
        
        self.val_buf     = np.zeros(buf_len, dtype='double')
        self.buf_count   = 0
        
        self.tpoint      = 0
        self.tstamp      = 0
        
        self.accumulator = 0
        self.total_count = 0

    def processing(self, tstamp):

        if not self.tpoint:
            self.tpoint = time.time()
            return False

        if self.tstamp:
            dt = (tstamp - self.tstamp)/1e8
            f  = 1/dt
            self.val_buf[self.buf_count] = f
            self.buf_count += 1
            
            if f > self.max:
                self.max = f

            if f < self.min:
                self.min = f
                
            if time.time() - self.tpoint > 1:
                self.tpoint = time.time()
                self.value  = self.val_buf[ :self.buf_count].mean()
                
                self.accumulator += self.val_buf.sum()
                self.total_count += self.buf_count
                self.mean         = self.accumulator/self.total_count
                
                self.sdev         = self.val_buf[ :self.buf_count].std()
                
                # reset tmp buffer
                self.val_buf.fill(0)
                self.buf_count = 0

                #
                self.tstamp = tstamp
                return True


        self.tstamp = tstamp
        return False


#-------------------------------------------------------------------------------
class AppMonitor(QObject):

    file_changed_signal = pyqtSignal( str )
    update_data_signal  = pyqtSignal( list )

    #-------------------------------------------------------    
    def __init__(self, fname):
        super().__init__()
        self.stamp       = 0
        self.fname       = fname
        self.frame_count = 0
        self.prev_fcount = 0

        self.dev_fps = FrameParam()
        
    #-------------------------------------------------------    
    def processing(self):
        stamp = os.stat(self.fname).st_mtime
        if stamp != self.stamp:
            self.stamp = stamp
            self.file_changed_signal.emit(self.fname)
        
    #-------------------------------------------------------
    def frame_slot(self, tstamp):
        self.frame_count += 1
        
        if self.dev_fps.processing(tstamp):
            self.update_data_signal.emit([self.dev_fps])

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
            self.monitor.processing()
            if self._finish_event.is_set():
                return
            
#-------------------------------------------------------------------------------
    
