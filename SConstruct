#-------------------------------------------------------------------------------
#
#     Main consctruction file
#
import os
import sys

from pathlib import Path

sys.path.append( '.scons' )

import helpers as hlp

#-------------------------------------------------------------------------------
#
#     Common settings
#
BOOST_VERSION = '1_84_0'

INCDIR        = [hlp.abspath('#src/include')]
BINDIR        = hlp.abspath('#bin')
BUILDPATH     = hlp.abspath('#build')
LIBDIR        = hlp.abspath('#lib')
LOGPATH       = hlp.abspath('#log')

DEFINES       = []

APP_SETTINGS = {
    'FRAME_SIZE_X'     : 640,
    'FRAME_SIZE_Y'     : 512,
    'VIDEO_DATA_WIDTH' : 14 # bit
}

#-------------------------------------------------------------------------------
#
#     Environment
#
env                  = Environment()
env['BOOST_VERSION'] = BOOST_VERSION

#-------------------------------------------------------------------------------
#
#     Platform-specific settings
#
Platform  = env['PLATFORM']
Toolchain = ARGUMENTS.get('toolchain', hlp.DEFAULT_TOOLCHAIN[Platform])

#------------------------------------------------------------
if Platform == 'win32':
    DEFINES.append('ENA_WIN_API')
elif Platform == 'posix':
    pass
else:
    print('E: scons: unsupported platform. Supported platforms are: "win32", "posix"')
    Exit(1)

#-------------------------------------------------------------------------------
#
#     Add user-defined options
#
AddOption('--verbose', action='store_true',  help='print full command lines of launched tools')

#-------------------------------------------------------------------------------
#
#     Setup construction environment
#

#     Process options and user's variables
if GetOption('verbose') == None:
    hlp.set_comstr(env)

#     Check build variant
Variant = ARGUMENTS.get('variant', 'release')

if not Variant in ['release', 'debug']:
    print('E: scons: invalid variant "%s" specified in command line. Supported variants are: "release", "debug"' % Variant)
    Exit(1)

#     Toolchain flags
CCFLAGS   = hlp.ccflags(Toolchain)
CXXFLAGS  = hlp.cxxflags(Toolchain)
OPTFLAGS  = hlp.optflags(Toolchain, Variant)

for k in APP_SETTINGS:
    DEFINES.append('{}={}'.format(k, APP_SETTINGS[k]))

env['VARIANT'] = Variant
env.Append(CPPPATH    = INCDIR)
env.Append(CCFLAGS    = CCFLAGS + OPTFLAGS)
env.Append(CXXFLAGS   = CXXFLAGS)
env.Append(CPPDEFINES = DEFINES)

env.Append(INCDIR    = INCDIR)
env.Append(BINDIR    = BINDIR / Variant)
env.Append(BUILDPATH = BUILDPATH / Variant)
env.Append(LIBPATH   = LIBDIR / Variant)
env.Append(LOGPATH   = LOGPATH)


if not LOGPATH.exists():
    Execute(Mkdir(LOGPATH))


#-------------------------------------------------------------------------------
#
#     Build hierarchy
#
SConscript('src/vframe/vframe.scons', 
            exports = 'env',
            variant_dir = '#build/%s/%s' % (env['VARIANT'], 'vframe' ), duplicate = 0)
#-------------------------------------------------------------------------------

