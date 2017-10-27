#!/usr/bin/env python3


import slon
import time

slon.init_numpy()
slon.init_frame()

f = slon.Frame()

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

