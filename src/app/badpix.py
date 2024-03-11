#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Detector/Sensor bad pixels handling
#
#    Copyright (c) 2016-2017, 2024, Camlab Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

import random

from PyQt5.QtCore import QObject, pyqtSignal

from logger import logger as lg

#-------------------------------------------------------------------------------
class TBadPix(QObject):

    def __init__(self):
        super().__init__()
        self.plist = []
        
#       for i in range(300):
#           x = random.randrange(1280 - 1)
#           y = random.randrange( 960 - 1)
#           self.plist.append( (x, y) )
        
        
    def toggle_pixel(self, pix):
        
        if pix in self.plist:
            self.plist.remove(pix)
        else:
            self.plist.append(pix)
            
    def pixels(self):
        return self.plist
        
#-------------------------------------------------------------------------------        
    
