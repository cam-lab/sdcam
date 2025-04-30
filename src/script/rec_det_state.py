import os
import time
import glob
import numpy as np

import threading
from logger import logger as lg


lock = threading.Lock()

#-------------------------------------------------------------------------------
class RecDetState:

    #-----------------------------------------------------------------
    def __init__(self):
        self.host   = None
        self.table  = []
        self.count  = 0
        
        self.mean   = 0
        self.rhlow  = 0
        self.rhhigh = 0
        
        self.k = 0.1
        
        self.title = 'VREF   VPB    VBB    ADVREF  FrameMean  HistoLow  HistoHigh'
        
        self.vbb_start   = 1000
        self.vbb_stop    = 1100
        self.vbb_step    = 1
        self.vbb         = self.vbb_start
        self.vbb_sweep   = False
        self.vbb_timeout = 0.5
        self.vbb_tpoint  = 0
        self.vbb_state   = 'set DAC'

    #-----------------------------------------------------------------
    def reset(self):

        self.table.clear()

    #-----------------------------------------------------------------
    def rec(self, n):
        lock.acquire()

        self.count  = n
        self.mean   = self.host._f.pixbuf.mean()
        self.rhlow  = self.host.rhlow
        self.rhhigh = self.host.rhhigh
        lg.info('begin record det state')
        self.t_start = time.time()

        lock.release()
        
    #-----------------------------------------------------------------
    def sweep(self, start, stop, step=1):
        self.reset()
        self.vbb_start = start
        self.vbb_stop  = stop
        self.vbb_step  = step
        self.vbb       = self.vbb_start
        self.vbb_sweep = True

    #-----------------------------------------------------------------
    def run(self, host):
        if not self.host:
            self.host = host

        if self.count:
            lock.acquire()
            self.mean   += self.k*(self.host._f.pixbuf.mean() - self.mean)
            self.rhlow  += self.k*(self.host.rhlow - self.rhlow)
            self.rhhigh += self.k*(self.host.rhhigh - self.rhhigh)
            self.count -= 1
            lock.release()

            if self.count == 0:
                rec = '{:4}   {:4}   {:4}   {:4} {:7} {:10} {:10}'.format(self.host.dac['VREF'][1],
                                                                          self.host.dac['VPB'][1],
                                                                          self.host.dac['VBB'][1],
                                                                          self.host.dac['ADVREF'][1],
                                                                          round(self.mean),
                                                                          round(self.rhlow),
                                                                          round(self.rhhigh))
                
                self.table.append(rec)
                dt = time.time() - self.t_start
                lg.info(f'stop record det state, time elapsed: {dt:.2f}')
                
        if self.vbb_sweep:
            if self.vbb_state == 'set DAC':
                lock.acquire()
                self.host.set_dac('VBB', self.vbb)
                lock.release()
                self.vbb_tpoint = time.time()
                self.vbb_state = 'wait'
                #lg.info('go to state "wait"')

            elif self.vbb_state == 'wait':
                t = time.time()
                #lg.info('t: {}, tpoing: {}, timeout: {}, t - tpoint: {}'.format(t, self.vbb_tpoint, self.vbb_timeout, t - self.vbb_tpoint))

                if  t - self.vbb_tpoint > self.vbb_timeout:
                    #lg.info('begin record')
                    self.rec(10)
                    self.vbb_state = 'record'
                    #lg.info('go to state "record"')

            elif self.vbb_state == 'record':
                if not self.count:
                    self.vbb += self.vbb_step
                    self.vbb_state = 'set DAC'
                    #lg.info('vbb: {}, vbb_stop: {}'.format(self.vbb, self.vbb_stop))
                    if self.vbb == self.vbb_stop:
                        self.vbb_sweep = False
                        lg.info(f'VBB sweep from {self.vbb_start} to {self.vbb_stop} with step {self.vbb_step} done')

    #-----------------------------------------------------------------
    def save(self, fname):
        out = self.title + os.linesep
        for s in self.table:
            out += s + os.linesep
            
        print(out)

        self.data = np.ndarray( (len(self.table), 7), dtype=np.uint32)
        for idx, item in enumerate(self.table):
            self.data[idx] = np.array(item.split(), dtype=np.uint32)

        with open(fname + '.rds', 'wb') as f:
            f.write(out.encode('utf-8'))
            
        self.data.tofile(fname +'.npdat')

#-------------------------------------------------------------------------------
def read(fname):
    data = np.fromfile(fname, dtype=np.uint32)
    return data.reshape(int(data.size/7), 7)

#-------------------------------------------------------------------------------
def vbb_responsivity(ext):
    flist = glob.glob(f'vps=*.{ext}')
    flist.sort()
    print(flist)

    vps      = []
    vbb_resp = []
    for fn in flist:
        data = read(fn)
        vps.append(data[0, 1])
        x    = data[:, 2]
        y    = data[:, 4]
        r    = np.polyfit(x, y, 1)
        vbb_resp.append(float(r[0]))

    return vps, vbb_resp

#-------------------------------------------------------------------------------

rds = RecDetState()
