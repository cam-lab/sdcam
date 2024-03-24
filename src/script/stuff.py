import time
import numpy as np

import threading
from logger import logger as lg


lock = threading.Lock()

class Frames:

    def __init__(self, c = 0):
        self.pool    = []
        self.count   = c

    def grab(self, n):
        lock.acquire()

        self.pool.clear()
        self.count = n
        lg.info('begin capture frames')
        self.t_start = time.time()

        lock.release()

    def run(self, host):
        if self.count:
            f = host._f.copy()
            lock.acquire()
            self.pool.append(f)
            self.count -= 1
            lock.release()

            if self.count == 0:
                dt = time.time() - self.t_start
                lg.info('stop capture frames, time elapsed: ' + '{:.2f}'.format(dt))


    def get_pix(self, row, col):
        return np.array([f.pixbuf[row, col] for f in self.pool], dtype='uint16')

f = Frames()
