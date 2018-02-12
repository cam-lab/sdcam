
import sys

import numpy as np
from matplotlib import pyplot as plt

sys.path.append('bin/release')

import vframe

vframe.init_numpy()

#f = np.fromfile('slon', dtype=np.uint32, sep=' ')
#h, b = np.histogram(f, bins=256, range=(0, 4096))


frame = vframe.TVFrame()
p = vframe.TPipeRxParams()
p.key = 2307
vframe.qpipe_cfg(p)
vframe.qpipe_get_frame(frame, p)

histo = np.zeros( (1024), dtype=np.uint32)

org, top, scale = vframe.histogram(frame.pixbuf, histo, 30)
