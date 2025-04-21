import os
import sys
import time
import glob
import queue
import collections
import datetime
import numpy as np
import matplotlib.pyplot as plt

import threading
from logger import logger as lg

BUFLEN = 16

thread_active = threading.Event()
sdc_msg_q     = collections.deque(maxlen=BUFLEN)

#-------------------------------------------------------------------------------
class VbbResp:

    #-----------------------------------------------------------------
    def __init__(self):
        self.host        = None
        
        self.FMEAN_MIN_L = 3000    # ADC LSBs
        self.FMEAN_MIN_H = 3500    # ADC LSBs
        self.FMEAN_MAX_L = 12000   # ADC LSBs
        self.FMEAN_MAX_H = 13000   # ADC LSBs
        
        #self.vbb_step    = 10      # mV
        
        self.res = []

    #-----------------------------------------------------------------
    def start(self, vpb_start=1500, vpb_stop=3500, vpb_step=30, dvbb=10):

        self.vpb_step             = vpb_step
        self.stop_flag            = False
        self.dvbb                 = dvbb
        
        self.vbbr_thread          = VbbRespThread()
        self.vbbr_thread.parent   = self
        self.vbbr_thread.host     = self.host
        self.vbbr_thread.vpb      = vpb_start
        self.vbbr_thread.vpb_max  = vpb_stop
        self.vbbr_thread.vpb_step = vpb_step
        self.vbbr_thread.dvbb     = dvbb
        self.vbbr_thread.fmean_l  = self.FMEAN_MIN_L
        self.vbbr_thread.fmean_h  = self.FMEAN_MIN_H
        self.vbbr_thread.start()
        thread_active.set()
        
    #-----------------------------------------------------------------
    def stop(self):
        self.stop_flag = True

    #-----------------------------------------------------------------
    def run(self, host):
        if thread_active.is_set():
            f = self.host._f.pixbuf.copy()
            sdc_msg_q.append( (f.mean(), self.host.dac) )

    #-----------------------------------------------------------------
    def summary(self, data):
        res = np.array(data, dtype=np.uint32)
        vpb = res[:, 0]
        vbb = res[:, 1]
        d   = res[:, 3] - res[:, 2]
        k   = d*0.12207/self.dvbb
        
        return res, vpb, vbb, d, k
            
    #-----------------------------------------------------------------
    def plot_res(self):
        res, vpb, vbb, d, k = self.summary(self.res)
        plt.plot(vpb, vbb, marker='.')

    #-----------------------------------------------------------------
    def save(self, path):
        res, x, y, d = self.summary(self.res)
        res.tofile(path)

    #-----------------------------------------------------------------
    def read(self, path):
        data = np.fromfile(path, dtype=np.uint32)
        
        # data is numpy array of uint32 items and  has the following format:
        #
        #    [VPB,   VBB,   Raw Histo Mean Low,   Raw Histo Mean High,  Raw Mean Delta ]
        #
        # data is 1D array after read from file and needs to be reshaped

        return data.reshape(int(data.size/4), 4)

#-------------------------------------------------------------------------------
class VbbRespThread(threading.Thread):
    #-----------------------------------------------------------------
    def __init__(self):
        super().__init__()
        
        self.VBB_MIN   = 1000    # mV
        self.VBB_MAX   = 3500    # mV

        self.fmean_buf = collections.deque(maxlen=BUFLEN)
        
    #-----------------------------------------------------------------
    def get_sdc_msg(self):
        self.fmean_buf.clear()
        time.sleep(0.3)
        n = 0
        while True:
            try:
                if sdc_msg_q:
                    fmean, dac = sdc_msg_q.pop()
                else:
                    time.sleep(0.1)
                    continue
            except:
                lg.info('get_sdc_msg: index error while read from queue')
                time.sleep(0.1)
                continue

            self.fmean_buf.append(fmean)
            n += 1
            if n >=BUFLEN:
                buf = np.array(self.fmean_buf, dtype=np.uint32)
                if buf.std() < 2:
                    #lg.info(f'get_sdc_msg: buf.mean: {int(buf.mean())}, buf.std: {int(buf.std())}')
                    return int(buf.mean()), dac

    #-----------------------------------------------------------------
    def set_vpb(self, vpb, vbb, vbb_min, vbb_max):

        lg.info('-'*40)
        lg.info(f'set VPB: {vpb}, vbb: {vbb}, vbb_min: {vbb_min}, vbb_max: {vbb_max}')
        self.host.set_dac('VPB', vpb)
        self.host.set_dac('VBB', vbb)
        
        fmean, dac = self.get_sdc_msg()
        vbb_l      = vbb_min # self.VBB_MIN
        vbb_h      = vbb_max # self.VBB_MAX
        
        step_cnt   = 0

        #lg.info(f'fmean: {fmean}, vbb: {vbb}')

        while fmean < self.fmean_l or fmean >  self.fmean_h:
            if self.parent.stop_flag:
                return fmean

            step_cnt += 1
            if fmean < self.fmean_l:
                vbb_l = vbb
                vbb   = (vbb + vbb_h) >> 1
                lg.info(f'{step_cnt:2} u, fmean: {fmean:5}, vbb: {vbb}, vbb_l: {vbb_l}')
            else:
                vbb_h = vbb
                vbb   = (vbb + vbb_l) >> 1
                lg.info(f'{step_cnt:2} o, fmean: {fmean:5}, vbb: {vbb}, vbb_h: {vbb_h}')

            self.host.set_dac('VBB', vbb)
            fmean, dac = self.get_sdc_msg()
            #lg.info(f'fmean: {fmean}, vbb: {vbb}')
                
        lg.info(f'Done => VBB: {vbb}, fmean: {fmean}, steps: {step_cnt}')
        lg.info('-'*40 + os.linesep)
        
        return fmean
        
    #-----------------------------------------------------------------
    def run(self):
        self.parent.res.clear()
        tstart    = time.time()
        self.stop = False
        k         = 1
        
        for vpb in range(self.vpb, self.vpb_max, self.vpb_step):
            if self.parent.stop_flag:
                break

            if vpb == self.vpb:
                #---------------------------------------------------------
                #
                #    Search VBB for initial point
                #
                lg.info(f'VPB: {vpb}, self.vpb: {self.vpb}')
                m0  = self.set_vpb(self.vpb, 2000, self.VBB_MIN, self.VBB_MAX)
                vbb = self.host.dac['VBB'][1]
            else:
                self.host.set_dac('VPB', vpb)
                m0, dac = self.get_sdc_msg()
                #lg.info(f'new point -> VPB: {vpb}, VBB: {vbb}, mean: {m1}')
                while m0 < self.fmean_l or m0 >  self.fmean_h:
                    if self.parent.stop_flag:
                        break

                    midpoint = (self.fmean_h + self.fmean_l) >> 1
                    vbb += int( round( (midpoint - m0)/k, 0 ) )
                    lg.info(f'mean: {m0}, midpoint: {midpoint}, k: {k}, miss: {midpoint - m0}, vbb: {vbb}')
                    self.host.set_dac('VBB', vbb)
                    m0, dac = self.get_sdc_msg()

            #-------------------------------------------------------------
            #
            #    Get response on VBB
            #
            #vbb += self.vpb_step
            self.host.set_dac('VBB', vbb + self.dvbb)
            m1, dac = self.get_sdc_msg()
            k       = round( (m1 - m0)/(self.dvbb), 3)
            self.host.set_dac('VBB', vbb)

            #-------------------------------------------------------------
            #
            #    Store result
            #
            self.parent.res.append( (vpb, vbb, m0, m1) )
            lg.info(f'>>>> VPB: {vpb}, VBB: {vbb}, k: {k}')

        if self.parent.stop_flag:
            lg.info('>>>>>>>>>> STOP BY USER <<<<<<<<<<<' + os.linesep)
        else:
            lg.info('>>>>>>>>>> DONE <<<<<<<<<<<' + os.linesep)
            
        dt = time.time() - tstart
        lg.info(f'time elapsed: {round(dt, 1)} ({str(datetime.timedelta(seconds=dt))})')

        thread_active.clear()

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

vbbr = VbbResp()

