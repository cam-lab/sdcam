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
     

vframe.init_numpy()

f = vframe.TVFrame()
p = vframe.TPipeRxParams()

p.key = 2307

vframe.qpipe_cfg(p)
print(p)

vframe.qpipe_get_frame(f, p)


