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

import collections

from   PyQt5.QtCore import QObject, pyqtSignal
from   logger import logger as lg

PERIOD = 0.1

#-------------------------------------------------------------------------------
class FrameParam:

    #-------------------------------------------------------
    def __init__(self, buf_len = 100):
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
        
        self.frame_count = 0

    #-------------------------------------------------------
    def reset(self):
        self.value       = 0
        self.mean        = 0
        self.min         = 1000
        self.max         = 0
        self.sdev        = 0

        self.val_buf.fill(0)
        self.buf_count   = 0

        self.tpoint      = 0
        self.tstamp      = 0

        self.accumulator = 0
        self.total_count = 0
        
        self.frame_count = 0

    #-------------------------------------------------------
    def processing(self, tstamp):

        self.frame_count += 1

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
class StatParam:
    #-------------------------------------------------------
    def __init__(self, min, max, buf_len = 16):
        self.buf = collections.deque(maxlen=buf_len)

        self.value       = 0
        self.mean        = 0
        self.min         = min
        self.max         = max
        self.sdev        = 0
        self.count       = 0
        
    #-------------------------------------------------------
    def reset(self):
        self.buf.clear()
        self.value       = 0
        self.mean        = 0
        self.min         = 100
        self.max         = -100
        self.sdev        = 0
        self.count       = 0
        
    def processing(self, temp):
        self.buf.append(temp)
        
        a = np.array(self.buf)
        self.value = temp
        self.mean  = a.mean()
        if a.min() < self.min:
            self.min = a.min()
            
        if a.max() > self.max:
            self.max = a.max()
            
        self.sdev = a.std()
        self.count += 1

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

        self.dev_fps   = FrameParam()
        self.sdc_fps   = FrameParam()
        self.fpa_temp  = StatParam(100, -100)
        self.forg      = StatParam(2**14, 0)
        self.fgain     = StatParam(30, 0)
        
        self._reset_stat_event = threading.Event()
        
    #-------------------------------------------------------
    def processing(self):
        stamp = os.stat(self.fname).st_mtime
        if stamp != self.stamp:
            self.stamp = stamp
            self.file_changed_signal.emit(self.fname)
        
    #-------------------------------------------------------
    def frame_slot(self, t):
        self.frame_count += 1
        
        tstamp, sdc_tpoint = t[0], t[1]

        if self._reset_stat_event.is_set():
            self._reset_stat_event.clear()
            self.dev_fps.reset()
            self.sdc_fps.reset()
            self.fpa_temp.reset()
            self.forg.reset()
            self.fgain.reset()
            self.update_data_signal.emit([0, self.dev_fps])
            self.update_data_signal.emit([1, self.sdc_fps])
            return

        if self.dev_fps.processing(tstamp):
            self.update_data_signal.emit([0, self.dev_fps])

        if self.sdc_fps.processing(sdc_tpoint):
            self.update_data_signal.emit([1, self.sdc_fps])

    #-------------------------------------------------------
    def fpa_temp_slot(self, temp):
        self.fpa_temp.processing(temp)
        self.update_data_signal.emit([2, self.fpa_temp])

    #-------------------------------------------------------
    def forg_slot(self, data):
        forg  = data[0]
        fgain = data[1]
        self.forg.processing(forg)
        self.fgain.processing(fgain)
        self.update_data_signal.emit([3, self.forg])
        self.update_data_signal.emit([4, self.fgain])

    #-------------------------------------------------------
    def reset_statistics(self):
        self._reset_stat_event.set()

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
    
