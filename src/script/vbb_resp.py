import os
import time
import glob
import queue
import collections
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
        self.host         = None
        
        self.VPB_MIN      = 1500    # mV
        self.VPB_MAX      = 3500    # mV

        self.FMEAN_MIN_L  = 3000    # ADC LSBs
        self.FMEAN_MIN_H  = 4000    # ADC LSBs
        self.FMEAN_MAX_L  = 12000   # ADC LSBs
        self.FMEAN_MAX_H  = 13000   # ADC LSBs

    #-----------------------------------------------------------------
    def start(self, vpb):
        self.vbbr_thread         = VbbRespThread()
        self.vbbr_thread.host    = self.host
        self.vbbr_thread.vpb     = vpb
        self.vbbr_thread.fmean_l = self.FMEAN_MIN_L
        self.vbbr_thread.fmean_h = self.FMEAN_MIN_H
        self.vbbr_thread.start()
        thread_active.set()
        
    #-----------------------------------------------------------------
    def run(self, host):
        if thread_active.is_set():
            sdc_msg_q.append( (self.host._f.pixbuf.mean(), self.host.dac) )

#-------------------------------------------------------------------------------
class VbbRespThread(threading.Thread):
    #-----------------------------------------------------------------
    def __init__(self):
        super().__init__()
        
        self.VBB_MIN   = 1000    # mV
        self.VBB_MAX   = 3500    # mV

        self.vpb       = 3000    # mV
        self.fmean_l   = 3000    # ADC LSBs
        self.fmean_h   = 4000    # ADC LSBs
        
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
    def set_vpb(self, val, vbb_min, vbb_max):

        lg.info('set VPB: {}, vbb_min: {}, vbb_max: {}'.format(val, vbb_min, vbb_max))
        self.host._set_dac('VBB', self.host.dac['VBB'][1])
        self.host._set_dac('VPB', val)
        
        fmean, dac = self.get_sdc_msg()
        vbb        = dac['VBB'][1]
        vbb_low    = self.VBB_MIN
        vbb_high   = self.VBB_MAX
        
        #lg.info('fmean: {}, vbb: {}'.format(fmean, vbb))

        while fmean < vbb_min or fmean > vbb_max:
            if fmean < vbb_min:
                vbb_low = vbb
                vbb     = (vbb + vbb_high) >> 1
                #lg.info('>>>> undershoot, vbb: {}, vbb_low: {}'.format(vbb, vbb_low))
            else:
                vbb_high = vbb
                vbb      = (vbb + vbb_low) >> 1
                #lg.info('>>>> overshoot, vbb: {}, vbb_high: {}'.format(vbb, vbb_high))

            self.host._set_dac('VBB', vbb)
            fmean, dac = self.get_sdc_msg()
            #lg.info('fmean: {}, vbb: {}'.format(fmean, vbb))
                
        lg.info('searching VBB done: VBB: {}, fmean: {}'.format(vbb, fmean))
        lg.info('-'*40 + os.linesep)
        self.host.dac_changed_signal.emit(0)
        
    #-----------------------------------------------------------------
    def run(self):
        self.set_vpb(self.vpb, self.fmean_l, self.fmean_h)
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
