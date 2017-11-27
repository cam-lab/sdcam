#!/usr/bin/env python3


import sys

sys.path.append('bin/release')
#sys.path.append('bin')

import vframe
import time

vframe.init_numpy()
vframe.init_frame()

f = vframe.Frame()

for i in range(400):
    t = f.read()
    fdata = f.data()
    t1 = time.monotonic()
    print('transfer: ', t1 - t)
    t2 = time.monotonic()
    #frame = fdata.reshape( 1280, 960 )
    t3 = time.monotonic()
    print('reshape: ', fdata.shape,  t3 - t2)
    
#   if i%20:
#       print(len(fdata), fdata[:10])

