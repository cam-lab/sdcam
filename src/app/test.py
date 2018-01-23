#!/usr/bin/env python3

import sys
import numpy as np
from matplotlib import pyplot as plt

sys.path.append('bin/release')

import vframe


class Formatter(object):
    def __init__(self, im):
        self.im = im
    def __call__(self, x, y):
        #z = self.im.get_array()[int(y), int(x)]
        return 'x={:.0f}, y={:.0f}'.format(x, y)
    
def imshow(f):
    fig, ax = plt.subplots()
    im = ax.imshow(f, cmap='gray')
    ax.format_coord = Formatter(im)
     

#-------------------------------------------------------------------------------
class TVFrame(QObject):

    frame_signal = pyqtSignal( np.ndarray )

    def __init__(self):
        super().__init__()
        self._pixmap = self.init_frame()
        self._n = 1000

        self._N = 0
        self._tsum = 0

        self._titles = ['numpy::rshift(4)  :',
                        'numpy::divide(16) :',
                        'C++::rshift(4)    :',
                        'C++::divide(16)   :']

        vframe.init_numpy()

        self._f = vframe.TVFrame()
        self._p = vframe.TPipeRxParams()

        self._p.key = 2307

        vframe.qpipe_cfg(self._p)
        print(self._p)


    def init_frame(self):
        return np.tile(np.arange(4095, step=32, dtype=np.uint16), [960, 10])

    def generate(self):
        t1 = time.time()
        self._pmap = np.right_shift( self._pixmap, 4 ).astype(dtype=np.uint8)
        t2 = time.time()
        #print(t2-t1)
        self._pmap[:, self._n] = 255
        if self._n < 1280-1:
            self._n += 1
        else:
            self._n = 0

        return self._pmap

    def read(self):
        vframe.qpipe_get_frame(self._f, self._p)

        if self._N >= 400:
            self._N = 0
            print('-'*20)

        t1 = time.time()
        if self._N < 100:
            self._pmap = np.right_shift( self._f.pixbuf, 4 ).astype(dtype=np.uint8)
        elif self._N < 200:
            self._pmap = (self._f.pixbuf/16).astype(dtype=np.uint8)
        elif self._N < 300:
            self._pmap = self._f.rshift(4)
            self._pmap = self._f.pixbuf.astype(dtype=np.uint8)
        elif self._N < 400:
            self._pmap = self._f.divide(16)
            self._pmap = self._f.pixbuf.astype(dtype=np.uint8)
        t2 = time.time()

        self._N += 1

        if not self._N % 100:
            idx = int(self._N/100) - 1
            print(self._titles[idx], self._tsum/100)
            self._tsum = t2-t1
        else:
            self._tsum += t2-t1

        return self._pmap


    def display(self):
        self.frame_signal.emit(self.read())


#-------------------------------------------------------------------------------
vframe.init_numpy()

f = vframe.TVFrame()
p = vframe.TPipeRxParams()

p.key = 2307

vframe.qpipe_cfg(p)
print(p)

vframe.qpipe_get_frame(f, p)

#-------------------------------------------------------------------------------


