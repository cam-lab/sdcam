import os
import time
import glob
import queue
import collections
import datetime
import numpy as np

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
        
        self.FMEAN_MIN_L = 6550    # ADC LSBs
        self.FMEAN_MIN_H = 6950    # ADC LSBs
        self.FMEAN_MAX_L = 12000   # ADC LSBs
        self.FMEAN_MAX_H = 13000   # ADC LSBs
        
        self.vbb_step    = 10      # mV
        
        self.res = []

    #-----------------------------------------------------------------
    def start(self, vpb=1500, vpb_max=3500, vpb_step=30):

        self.vpb_step             = vpb_step
        self.stop_flag            = False
        
        self.vbbr_thread          = VbbRespThread()
        self.vbbr_thread.parent   = self
        self.vbbr_thread.host     = self.host
        self.vbbr_thread.vpb      = vpb
        self.vbbr_thread.vpb_max  = vpb_max
        self.vbbr_thread.vpb_step = vpb_step
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
        x   = res[:, 0]
        y   = (res[:, 3] - res[:, 2])*0.12207/self.vbb_step
        
        return res, x, y
            
    #-----------------------------------------------------------------
    def save(self, path):
        res, x, y = self.summary(self.res)
        res.tofile(path)

    #-----------------------------------------------------------------
    def read(self, path):
        data = np.fromfile(path, dtype=np.uint32)
        
        # data is numpy array of uint32 items and  has the following format:
        #
        #    [VPB,   VBB,   Raw Histo Mean at VBB-30mV,   Raw Histo Mead at VBB]
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
                if buf.std() < 10:
                    #lg.info('get_sdc_msg: buf.mean: {}, buf.std: {}'.format(int(buf.mean()), int(buf.std())))
                    return int(buf.mean()), dac

    #-----------------------------------------------------------------
    def set_vpb(self, vpb, vbb, vbb_min, vbb_max):

        lg.info('-'*40)
        lg.info('set VPB: {}, vbb: {}, vbb_min: {}, vbb_max: {}'.format(vpb, vbb, vbb_min, vbb_max))
        self.host.set_dac('VBB', vbb)
        self.host.set_dac('VPB', vpb)
        
        fmean, dac = self.get_sdc_msg()
        vbb_l      = vbb_min # self.VBB_MIN
        vbb_h      = vbb_max # self.VBB_MAX
        
        step_cnt   = 0

        #lg.info('fmean: {}, vbb: {}'.format(fmean, vbb))

        #while fmean < vbb_min or fmean > vbb_max:
        while fmean < self.fmean_l or fmean >  self.fmean_h:
            if self.parent.stop_flag:
                return fmean

            step_cnt += 1
            if fmean < self.fmean_l:
                vbb_l = vbb
                vbb   = (vbb + vbb_h) >> 1
                #lg.info('{:2} u, fmean: {:5}, vbb: {}, vbb_l: {}'.format(step_cnt, fmean, vbb, vbb_l))
            else:
                vbb_h = vbb
                vbb   = (vbb + vbb_l) >> 1
                #lg.info('{:2} o, fmean: {:5}, vbb: {}, vbb_h: {}'.format(step_cnt, fmean, vbb, vbb_h))

            self.host.set_dac('VBB', vbb)
            fmean, dac = self.get_sdc_msg()
            #lg.info('fmean: {}, vbb: {}'.format(fmean, vbb))
                
        lg.info('Done => VBB: {}, fmean: {}, steps: {}'.format(vbb, fmean, step_cnt))
        lg.info('-'*40 + os.linesep)
        
        return fmean
        
    #-----------------------------------------------------------------
    def run(self):
        self.parent.res.clear()
        first     = True
        vbb       = 0
        vbb_step  = 10
        tstart    = time.time()
        self.stop = False
        
        if self.vpb_max:
            for vpb in range(self.vpb, self.vpb_max, self.vpb_step):
                if self.parent.stop_flag:
                    break

                if first:
                    first = False
                    vbb   = 2000
                    vbb_h = self.VBB_MAX
                    vbb_l = self.VBB_MIN
                else:
#                   vbb_h = vbb - vbb_step + 3
#                   vbb_l = vbb - vbb_step*2
                    vbb_h = vbb - vbb_step
                    vbb_l = vbb - self.vpb_step*2
                
                #m0 = self.set_vpb(vpb, self.fmean_l, self.fmean_h)
                m0 = self.set_vpb(vpb, vbb, vbb_l, vbb_h)
                vbb = self.host.dac['VBB'][1] + vbb_step
                self.host._set_dac('VBB', vbb)
                m1, dac = self.get_sdc_msg()
                self.parent.res.append( (self.host.dac['VPB'][1], self.host.dac['VBB'][1], m0, m1) )
        else:
            self.set_vpb(self.vpb, self.fmean_l, self.fmean_h)
            
        if self.parent.stop_flag:
            lg.info('>>>>>>>>>> STOP BY USER <<<<<<<<<<<' + os.linesep)
        else:
            lg.info('>>>>>>>>>> DONE <<<<<<<<<<<' + os.linesep)
            
        dt = time.time() - tstart
        lg.info('time elapsed: {} ({})'.format(round(dt, 1), str(datetime.timedelta(seconds=dt))))

        thread_active.clear()

#-------------------------------------------------------------------------------
def read(fname):
    data = np.fromfile(fname, dtype=np.uint32)
    return data.reshape(int(data.size/7), 7)

#-------------------------------------------------------------------------------
def vbb_responsivity(ext):
    flist = glob.glob('vps=*.{}'.format(ext))
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
