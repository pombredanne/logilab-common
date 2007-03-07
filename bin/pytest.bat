@echo off
rem = """-*-Python-*- script
rem -------------------- DOS section --------------------
rem You could set PYTHONPATH or TK environment variables here
python -x %~f0 %*
goto exit
 
"""
# -------------------- Python section --------------------
import os, sys
import os.path as osp
from logilab.common import testlib

curdir = os.getcwd()
if osp.exists(osp.join(curdir, '__pkginfo__.py')):
    projdir = osp.abspath(curdir)
elif osp.exists(osp.join(curdir, '..')):
    projdir = osp.abspath(osp.join(curdir, '..'))
else:
    print 'fixme: cannot be run from here.'
    sys.exit(1)
testlib.main(osp.join(projdir,'test'))
 

DosExitLabel = """
:exit
rem """


