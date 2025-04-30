import os
import time
import numpy as np

import threading
from logger import logger as lg


lock = threading.Lock()

#-------------------------------------------------------------------------------
class Frames:

    #-----------------------------------------------------------------
    def __init__(self, raw=False):
        self.pool  = []
        self.count = 0
        self.raw   = raw
        
    #-----------------------------------------------------------------
    #
    #    Begin grabbing series of pixel data of the video frames
    #
    #    Arg:
    #    ~~~
    #       Required frame count
    #
    def grab(self, n):
        with lock:
            self.pool.clear()
            self.count = n
            lg.info('begin capture frames')
            self.t_start = time.time()

    #-----------------------------------------------------------------
    #
    #    Return numpy array of the pixel values from specified position
    #    along of all frames in grabbed series
    #
    #    Args:
    #    ~~~~
    #      Row and column indices of the pixel
    #
    def get_pix(self, row, col):
        return np.array([f[row, col] for f in self.pool], dtype='uint16')

    #-----------------------------------------------------------------
    #
    #    Return numpy array of the rows from specified row position
    #    along of all frames in grabbed series
    #
    #    Arg:
    #    ~~~
    #      Row index
    #
    def get_row(self, row):
        return np.array([f[row] for f in self.pool], dtype='uint16')

    #-----------------------------------------------------------------
    #
    #    Return numpy array of the columns from specified column position
    #    along of all frames in grabbed series
    #
    #    Arg:
    #    ~~~
    #      Colunm index
    #
    def get_col(self, col):
        return np.array([f[:, col] for f in self.pool], dtype='uint16')

    #-----------------------------------------------------------------
    #
    #    Capture specified count of the series of frames and save
    #    data of each series in separate file
    #
    #    Args:
    #    ~~~~
    #      Series count: how many series need to be grabbed
    #                    seriens length - length (frame count) of each series
    #
    #      Base path:  path where data should be saved
    #
    #    Example:
    #    ~~~~~~~
    #      Capture 10 series with 100 frames each and put them on the specified path
    #
    #        fcap.capt_series(10, 100, 'det/r2313b-70')
    #
    def capt_series(self, scount, slen, basepath):
        self.sercount    = scount
        self.serlen      = slen
        self.serbasepath = basepath
        
        self.capt_series_thread = threading.Thread(target=self.capt_series_exec)
        self.capt_series_thread.start()

    #-----------------------------------------------------------------
    #    Internals
    #-----------------------------------------------------------------
    def capt_series_exec(self):

        for i in range(self.sercount):
            self.host.nuc.launch()
            time.sleep(1)
            self.grab(self.serlen)
            while self.count:
                time.sleep(1)
                
            np.save(os.path.join(self.serbasepath, f'f{self.serlen}-{i:03}.npy'), self.pool)

    #-----------------------------------------------------------------
    def run(self, host):
        if self.count:
            if self.raw:
                f = host._f.pixbuf.copy()
            else:
                f = host.df.copy()

            with lock:
                self.pool.append(f)
                self.count -= 1

            if self.count == 0:
                dt = time.time() - self.t_start
                lg.info('stop capture frames, time elapsed: ' + f'{dt:.2f}')

#-------------------------------------------------------------------------------

fcap = Frames()

