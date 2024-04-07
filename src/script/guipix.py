import numpy as np

class Display:

    def __init__(self, sdcam):
        self.sdc = sdcam.vfthread.core
        self.mw  = sdcam.mwin
        self.pi  = self.mw.PixmapItem
        self.pm  = self.pi.pixmap()
        self.img = self.pm.toImage()

    def pix(self, x, y):

        self.pc = self.img.pixelColor(x, y)
        self.pixel = self.img.pixel(x, y)

        print('pix value:', self.pc.value(), 'rgb:', hex(self.pixel), 'rgb val:',
              self.pixel & 0xff, (self.pixel >> 8) & 0xff, (self.pixel >> 16) & 0xff )


    def pmap(self, x, y):
        pixel = self.sdc._pmap[x][y]
        print('pmap:', pixel & 0x3ff, (pixel >> 10) & 0x3ff, (pixel >> 20) & 0x3ff )

