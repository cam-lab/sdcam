#-------------------------------------------------------------------------------
#
#    Project: Software-Defined Camera
#
#    Purpose: Device Remote Control
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

import os
import numpy as np

vhex = np.vectorize(hex)


ID_NUMBER_MASK                = 0x00ff
ID_TYPE_MASK                  = 0x7f00
ID_RESPONSE_MASK              = 0x7f00
ID_ORG_MASK                   = 0x8000
MMR_IDX_MASK                  = 0x03ff
MOD_IDX_MASK                  = ~MMR_IDX_MASK & 0xffff
OPCODE_MASK                   = 0x00ff
PCOUNT_MASK                   = 0xff00

ID_NUMBER_OFFSET              = 0
ID_TYPE_OFFSET                = 8
ID_ORG_OFFSET                 = 15
ID_RESPONSE_OFFSET            = ID_TYPE_OFFSET
MOD_IDX_OFFSET                = 10
PCOUNT_OFFSET                 = 8

resp_code = { }

resp_code[0] = 'Ok'
resp_code[1] = 'malformed request message'
resp_code[2] = 'unsupported module index'
resp_code[3] = 'invalid MMR index for specified module'
resp_code[4] = 'unsupported operation code'
resp_code[5] = 'incorrect parameter count for specified operation'
resp_code[6] = 'invalid parameter value for specified operation'
CAMERA_ENA_MASK     = 0x0001
VFG_ENA_MASK        = 0x0002

MMR_WRITE                     = 1
MMR_READ                      = 2
FUN_EXEC                      = 3
DEV_NOTIFY                    = 4

class SysMod:
    def __init__(self):
        self._mod = 0
        self._cr  = 0
    
    def cr(self): return (self._mod << MOD_IDX_OFFSET) + self._cr
    
class CamMod:
    def __init__(self):
        self._mod  = 1
        self._cr   = 0
        self._cr_s = 1
        self._cr_c = 2
        self._sr   = 3
    
    def cr(self):   return (self._mod << MOD_IDX_OFFSET) + self._cr
    def cr_s(self): return (self._mod << MOD_IDX_OFFSET) + self._cr_s
    def cr_c(self): return (self._mod << MOD_IDX_OFFSET) + self._cr_c
    def sr(self):   return (self._mod << MOD_IDX_OFFSET) + self._sr


class LanMod:
    def __init__(self):
        self._mod     = 3
        self._cr      = 0
        self._cr_s    = 1
        self._cr_c    = 2
        self._sr      = 3
        self._mdio    = 4
        self._mac_l   = 6
        self._mac_h   = 7
        self._dev_ip  = 8
        self._host_ip = 9
    
    def cr(self):      return (self._mod << MOD_IDX_OFFSET) + self._cr
    def cr_s(self):    return (self._mod << MOD_IDX_OFFSET) + self._cr_s
    def cr_c(self):    return (self._mod << MOD_IDX_OFFSET) + self._cr_c
    def sr(self):      return (self._mod << MOD_IDX_OFFSET) + self._sr
    def mdio(self):    return (self._mod << MOD_IDX_OFFSET) + self._mdio
    def mac_l(self):   return (self._mod << MOD_IDX_OFFSET) + self._mac_l
    def mac_h(self):   return (self._mod << MOD_IDX_OFFSET) + self._mac_h
    def dev_ip(self):  return (self._mod << MOD_IDX_OFFSET) + self._dev_ip
    def host_ip(self): return (self._mod << MOD_IDX_OFFSET) + self._host_ip


class LensMod:
    def __init__(self):
        self._mod = 4
        self._cr  = 0

    def cr(self): return (self._mod << MOD_IDX_OFFSET) + self._cr
    
sysmod = SysMod()
cam    = CamMod()
lan    = LanMod()
lens   = LensMod()


def check_resp(num, resp):
    if not resp:
        print('E: no response from device. Be sure the device is online')
        return False

    if len(resp) == 0:
        print( 'E: invalid response length: {}'.format( len(resp), os.linesep ) )
        print(vhex(resp))
        return False

    id = resp[0]
    
    if num != id & ID_NUMBER_MASK:
        print( 'E: incorrect message number: {}'.format( id & ID_NUMBER_MASK, os.linesep ) )
        print(vhex(resp))
        return False

    rc = (id & ID_RESPONSE_MASK) >> ID_RESPONSE_OFFSET
    if rc > len(resp_code):
        print( 'E: unknown response code: {}'.format( rc, os.linesep ) )
        print(vhex(resp))
        return False
        
    if rc != 0:
        print( 'E: request returns error code: "{}"'.format( resp_code[rc], os.linesep ) )
        print(vhex(resp))
        return False

    return True

