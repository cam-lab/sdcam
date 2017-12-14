#-------------------------------------------------------------------------------
#
#     Main consctruction file
#
import os
import sys

sys.path.append( '.scons' )

from helpers import *

#-------------------------------------------------------------------------------
#
#     Common settings
#
QTDIR      = os.environ['QT5DIR']
INCDIR     = ['#inc', '#src/include']
BINDIR     = '#bin'
BUILDROOT  = '#build'
LIBDIR     = '#lib'
DEFINES    = []
env        = Environment()

#-------------------------------------------------------------------------------
#
#     Platform-specific settings
#
Platform  = env['PLATFORM']
Toolchain = ARGUMENTS.get('toolchain', DEFAULT_TOOLCHAIN[Platform])

#------------------------------------------------------------
if Platform == 'win32':
    DEFINES  += ['ENA_WIN_API']
elif Platform == 'posix':
    DEFINES += []
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
    set_comstr(env)

#     Check build variant
Variant = ARGUMENTS.get('variant', 'release')

if not Variant in ['release', 'debug']:
    print('E: scons: invalid variant "%s" specified in command line. Supported variants are: "release", "debug"' % Variant)
    Exit(1)

#     Toolchain flags
CCFLAGS   = ccflags(Toolchain)
CXXFLAGS  = cxxflags(Toolchain)
OPTFLAGS  = optflags(Toolchain, Variant)

#     Qt environment
qtEnv = env.Clone()
qtEnv['VARIANT'] = Variant
qtEnv['ENV']['PKG_CONFIG_PATH'] = os.path.join(QTDIR, 'lib/pkgconfig')
qtEnv['QT5DIR'] = QTDIR
qtEnv.Append(CPPPATH   = INCDIR)
qtEnv.Append(CCFLAGS   = CCFLAGS + OPTFLAGS)
qtEnv.Append(CXXFLAGS  = CXXFLAGS)
qtEnv.Append(INCDIR    = INCDIR)
qtEnv.Append(BINDIR    = os.path.join(BINDIR, Variant))
qtEnv.Append(BUILDROOT = os.path.join(BUILDROOT, Variant))
qtEnv.Append(LIBPATH   = os.path.join(LIBDIR, Variant))
qtEnv.Tool('qt5')

#-------------------------------------------------------------------------------
#
#     Build hierarchy
#
SConscript('src/vframe/vframe.scons', 
            exports = 'qtEnv',
            variant_dir = '#build/%s/%s' % (qtEnv['VARIANT'], 'vframe' ), duplicate = 0)
SConscript('src/qpipe/SConscript', exports = 'qtEnv')
#-------------------------------------------------------------------------------

