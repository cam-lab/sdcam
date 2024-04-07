#-------------------------------------------------------------------------------
#
#
#
import os
import sys
import psutil

from pathlib import Path

import SCons 

from SCons.Script import *

from cfg import *
#-------------------------------------------------------------------------------
COMSTR = \
{
    'cc'     : 'cc  ',
    'cxx'    : 'cxx ',
    'link'   : 'link',
    'lib'    : 'lib ',
    'ranlib' : 'idx ',   
    'qt5moc' : 'moc ', 
    'qt5qrc' : 'qrc ' 
}
#-------------------------------------------------------------------------------
def abspath(p):
    return Path(Dir(p).abspath)
#-------------------------------------------------------------------------------
def ccflags(toolchain):
    return TOOLCHAIN_CCFLAGS[toolchain]
#-------------------------------------------------------------------------------
def cxxflags(toolchain):
    return TOOLCHAIN_CXXFLAGS[toolchain]
#-------------------------------------------------------------------------------
def optflags(toolchain, variant):
    return TOOLCHAIN_OPTFLAGS[toolchain][variant]
#-------------------------------------------------------------------------------
def shell_support_colors():
    parent = psutil.Process().parent().name()
    
    if any( shell_name in parent for shell_name in ('bash',  'zsh', 'cmd.exe') ): 
        return True
    else:
        return False
        
#-------------------------------------------------------------------------------
def colorize(s, color):
    if shell_support_colors():
        ESC = '\033['
        colors = {}
        colors['black']    = '1;30'
        colors['red']      = '1;31'
        colors['green']    = '1;32'
        colors['yellow']   = '0;33'
        colors['blue']     = '1;34'
        colors['magenta']  = '1;35'
        colors['cyan']     = '1;36'
        colors['white']    = '1;37'
    
        return ESC + colors[color] + 'm' + s + ESC + '0m'
    else:
        return s
#-------------------------------------------------------------------------------
def set_comstr(env):
    env['CCCOMSTR']      = colorize('%s : $SOURCE' % COMSTR['cc'],    'white'  ) 
    env['SHCCCOMSTR']    = colorize('%s : $SOURCE' % COMSTR['cc'],    'white'  ) 
    env['CXXCOMSTR']     = colorize('%s : $SOURCE' % COMSTR['cxx'],   'white'  ) 
    env['SHCXXCOMSTR']   = colorize('%s : $SOURCE' % COMSTR['cxx'],   'white'  ) 
    env['LINKCOMSTR']    = colorize("%s : $TARGET" % COMSTR['link'],  'green'  )
    env['SHLINKCOMSTR']  = colorize("%s : $TARGET" % COMSTR['link'],  'green'  )
    env['ARCOMSTR']      = colorize('%s : $TARGET' % COMSTR['lib'],   'magenta')
    env['RANLIBCOMSTR']  = colorize('%s : $TARGET' % COMSTR['ranlib'],'magenta')
    env['QT5_MOCCOMSTR'] = colorize('%s : $SOURCE' % COMSTR['qt5moc'],'yellow' )  
    env['QT5_QRCCOMSTR'] = colorize('%s : $SOURCE' % COMSTR['qt5qrc'],'blue'   )  
#-------------------------------------------------------------------------------
def explicit_moc(env, moc_files):
    RootDir = str(env.Dir('#'))
    trg_src_pairs = []
    for d in moc_files.keys():
        src_dir = os.path.join(RootDir, d)
        dst_dir = os.path.join( env['BUILDDIR'], d)
        for f in moc_files[d]:
            src = os.path.join(src_dir, f)
            dst = os.path.join(dst_dir, f + '.cc')
            trg_src_pairs.append( (dst, src) )
    
    moc_nodes = []
    for i in trg_src_pairs:
        moc_nodes.append( env.ExplicitMoc5( i[0], i[1] ) )
        
    return moc_nodes
#-------------------------------------------------------------------------------
def qrc(env, qrc_files):
    dst_dir = os.path.join( env['BUILDDIR'], os.path.split(env['CURDIR'])[1] )
    qrc_nodes = []
    for f in qrc_files:
        dst_name = os.path.join(dst_dir, f + '.cc')
        qrc_nodes.append(env.Qrc5(dst_name, f))
    
    return qrc_nodes
#-------------------------------------------------------------------------------


