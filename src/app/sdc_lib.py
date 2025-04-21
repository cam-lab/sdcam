#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Camera Components
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

import matplotlib.pyplot as plt
import collections

from PyQt5.QtCore import QObject, pyqtSignal

import sys

from logger import logger as lg
import vframe
#import gui

#from udp import command_queue, Socket, HOST_IP, DEVICE_IP, DRC_PORT

import drc
 
#iframe_event          = threading.Event()
#vsthread_finish_event = threading.Event()

#-------------------------------------------------------------------------------
class Nuc:
    def __init__(self, host):
        self.lock      = threading.Lock()
        self.host      = host
        self.prep_rqst = False
        self.fcnt      = 0
        self.fpool     = []
        self.cframe    = None
        self.valid     = False
        
        self.apply     = False
        
        self.shtr_begin_line = 10
        
        self.afcount   = 2

    def launch(self):
        with self.lock:
        
            self.fcnt       = 0;
            self.fpool      = []
            self.prep_rqst  = True

            self.host._wmmr(drc.cam.cr_c, 7 << 16)
            if self.host._wmmr(drc.cam.cr_s, (self.afcount + 1) << 16):
                lg.info(f'successful set shuttered frame count to {self.afcount}')
            else:
                lg.warning('set shuttered frame count failed')

            return self.host._wmmr(drc.cam.shtr, self.shtr_begin_line)  # return status for check MMR write acknoledge

    def processing(self):
        if self.prep_rqst:
            self.prep_cf()

    def prep_cf(self):
        f = self.host._f.copy()

        self.fpool.append(f)
        if f.shtr_on():
                
            self.fcnt += 1
            if self.fcnt == 2:
                self.cframe = self.host._f.pixbuf.copy()
                lg.info(f'{self.fcnt} blinded frame')
            elif self.fcnt > 2 and self.fcnt <= self.afcount + 1:
                self.cframe += self.host._f.pixbuf
                lg.info(f'{self.fcnt} blinded frame')
                if self.fcnt == self.afcount + 1:
                    self.cframe = (self.cframe/self.afcount).astype(np.uint16)
                    lg.info('cframe complete')
                    self.valid  = True

        elif self.fcnt:
            if not f.shtr_on():
                self.prep_rqst = False
                s = ' '.join([str(int(f.shtr_on())) for f in self.fpool])
                lg.info(f'NUC complete, frames {len(self.fpool)}, {s}')
                
                shtr_end_line = self.host._rmmr(drc.cam.shtr)
                shtr_begin_line = self.shtr_begin_line
                
                lg.info(f'bl: {shtr_begin_line}, el: {shtr_end_line}, bl_new: {self.shtr_begin_line}')

#-------------------------------------------------------------------------------
class BiasManager(threading.Thread):
    def __init__(self, host):
        super().__init__()
        
        self._finish_event = threading.Event()

        self.host           = host
        self.MIDDLE         = 2**14 >> 1
        self.TRACKING_SPAN  = 2000
        self.SETUP_SPAN     = 200
        self.BUFLEN         = 16

        self.span           = self.SETUP_SPAN
        self.fmean_incoming = threading.Condition()
        self.fmean_buf      = collections.deque(maxlen=self.BUFLEN)
        
        self.vbp_vbb_poly   = np.array([-6.36482083e-05, -4.87290592e-01,  4.00794667e+03 + 15])
        self.vbb_gain       = 40/0.12207
        
        self.vpb            = 3000
        self.vbb            = int(np.polyval(self.vbp_vbb_poly, self.vpb))
        
        self.state          = 'TRACKING'
        

    def finish(self):
        self._finish_event.set()

    def run(self):
        self.host.set_dac('VPB', self.vpb)
        self.host.set_dac('VBB', self.vbb)
        self.fmean_buf.clear()
        lg.info('Bias Mgr: setup VPB')
        
        while True:
            if self._finish_event.is_set():
                return

            with self.fmean_incoming:
                res = self.fmean_incoming.wait(1)
#               if not res:
#                   lg.info('Bias Manager thread timeout')
#                   continue

                buf = np.array(self.fmean_buf, dtype=np.uint32)
                
                if buf.size < self.BUFLEN or buf.std() > 100:
                    continue

                mean = buf.mean()
                
                if mean < 5 or mean > 2**14 - 5:
                    if self.state == 'TRACKING':
                        self.vbb = int(np.polyval(self.vbp_vbb_poly, self.vpb))
                        self.host.set_dac('VBB', self.vbb); self.fmean_buf.clear()
                        self.state = 'SETUP'
                        lg.info(f'Bias Mgr: set initial VBB point at {self.vbb}')

                    else:
                        if mean < 5:
                            self.vbb += 10
                            lg.info('Bias Mgr: VBB miss, move VBB point up with 10 mV step')
                        else:
                            self.vbb -= 10
                            lg.info('Bias Mgr: VBB miss, move VBB point down with 10 mV step')
                            
                        self.host.set_dac('VBB', self.vbb); self.fmean_buf.clear()

                elif self.state == 'SETUP':
                    if abs(self.MIDDLE - mean) > self.SETUP_SPAN:
                        dvbb = int( round( (self.MIDDLE - mean)/self.vbb_gain, 0 ) )
                        self.vbb += dvbb
                        self.host.set_dac('VBB', self.vbb); self.fmean_buf.clear()
                        lg.info(f'Bias Mgr: correct VBB point with {dvbb} mV')
                    else:
                        self.state = 'TRACKING'
                        self.host.nuc.launch()
                        lg.info('Bias Mgr: output signal in range!')
                    
                else:
                    if abs(self.MIDDLE - mean) > self.TRACKING_SPAN:
                        lg.info('Bias Mgr: output signal out of range!')
                        self.state = 'SETUP'

#-------------------------------------------------------------------------------
class Histogram:
    def __init__(self, size):
        self.data    = np.zeros(size, dtype=np.uint32)
        self.max     = 0
        self.org     = 0
        self.top     = size-1
        self.k       = 0.1

    def update(self, f):
        self.data.fill(0)
        vframe.histo(f, self.data, 1)
        self.max += self.k*(self.data[1:-1].max() - self.max)

#-------------------------------------------------------------------------------
def plot_frame_hist(pbuf):
    plt.cla()
    plt_histo = np.zeros(2**14, dtype=np.uint32)
    fframe_org, fframe_top, fframe_scale = vframe.histogram(pbuf, plt_histo, 1, 1, 0)
    plt.plot(plt_histo)
    #self.ax.bar(np.arange(fframe_org, fframe_top), self.plt_histo[fframe_org:fframe_top])
    #val, edge = np.histogram(pbuf, bins=10)
    #self.ax.bar(edge[:-1], val)

#-------------------------------------------------------------------------------
def average_frame(buf, n=16):
    if n > 16:
        lg.warning(f'invalid frame count {n}, max count: 16')
        return None

    pool = buf[0].copy().astype(np.uint32)

    for i in range(n-1):
        pool += buf[i+1]

    p = (pool/n).astype(np.uint16)

    return p

#-------------------------------------------------------------------------------
def histo_bounds(f, org, top, thld):
    b = np.where(f >= thld)[0][1:-1]

    if not b.size:
        return org, top

    min = b.min()
    max = b.max()

    k = 0.1

    org += k*(min - org)
    top += k*(max - top)

    return int(org), int(top)

#-------------------------------------------------------------------------------

