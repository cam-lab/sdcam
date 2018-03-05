

import random

from PyQt5.QtCore import QObject, pyqtSignal

from logger import logger as lg

#-------------------------------------------------------------------------------
class TBadPix(QObject):

    def __init__(self):
        super().__init__()
        self.plist = []
        
        for i in range(300):
            x = random.randrange(1280 - 1)
            y = random.randrange( 960 - 1)
            self.plist.append( (x, y) )
        
        
    def toggle_pixel(self, pix):
        
        if pix in self.plist:
            self.plist.remove(pix)
        else:
            self.plist.append(pix)
            
    def pixels(self):
        return self.plist
        
#-------------------------------------------------------------------------------        
    
