"""shell/term utilities, useful to write some python scripts instead of shell
scripts.

:author:    Logilab
:copyright: 2000-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

import os        
import glob
import shutil
import sys
import tempfile
import time
from os.path import exists, isdir, islink, basename, join, walk

from logilab.common import STD_BLACKLIST


def chown(path, login=None, group=None):
    """Same as `os.chown` function but accepting user login or group name as
    argument. If login or group is omitted, it's left unchanged.

    Note: you must own the file to chown it (or be root). Otherwise OSError is raised. 
    """
    if login is None:
        uid = -1
    else:
        try:
            uid = int(login)
        except ValueError:
            import pwd
            uid = pwd.getpwnam(login).pw_uid
    if group is None:
        gid = -1
    else:
        try:
            gid = int(group)
        except ValueError:
            import grp
            gid = grp.getgrname(group).gr_gid
    os.chown(path, uid, gid)
        

def mv(source, destination, _action=shutil.move):
    """A shell-like mv, supporting wildcards.
    """
    sources = glob.glob(source)
    if len(sources) > 1:
        assert isdir(destination)
        for filename in sources:
            _action(filename, join(destination, basename(filename)))
    else:
        try:
            source = sources[0]
        except IndexError:
            raise OSError('No file matching %s' % source)
        if isdir(destination) and exists(destination):
            destination = join(destination, basename(source))
        try:
            _action(source, destination)
        except OSError, ex:
            raise OSError('Unable to move %r to %r (%s)' % (
                source, destination, ex))
        
def rm(*files):
    """A shell-like rm, supporting wildcards.
    """
    for wfile in files:
        for filename in glob.glob(wfile):
            if islink(filename):
                os.remove(filename)
            elif isdir(filename):
                shutil.rmtree(filename)
            else:
                os.remove(filename)
    
def cp(source, destination):
    """A shell-like cp, supporting wildcards.
    """
    mv(source, destination, _action=shutil.copy)


def find(directory, exts, exclude=False, blacklist=STD_BLACKLIST):
    """Recursivly find files ending with the given extensions from the directory.

    :type directory: str
    :param directory:
      directory where the search should start

    :type exts: basestring or list or tuple
    :param exts:
      extensions or lists or extensions to search

    :type exclude: boolean
    :param exts:
      if this argument is True, returning files NOT ending with the given
      extensions

    :type blacklist: list or tuple
    :param blacklist:
      optional list of files or directory to ignore, default to the value of
      `logilab.common.STD_BLACKLIST`

    :rtype: list
    :return:
      the list of all matching files
    """
    if isinstance(exts, basestring):
        exts = (exts,)
    if exclude:
        def match(filename, exts):
            for ext in exts:
                if filename.endswith(ext):
                    return False
            return True
    else:
        def match(filename, exts):
            for ext in exts:
                if filename.endswith(ext):
                    return True
            return False
    def func(files, directory, fnames):
        """walk handler"""
        # remove files/directories in the black list
        for norecurs in blacklist:
            try:
                fnames.remove(norecurs)
            except ValueError:
                continue
        for filename in fnames:
            src = join(directory, filename)
            if isdir(src):
                continue
            if match(filename, exts):
                files.append(src)
    files = []
    walk(directory, func, files)
    return files


def unzip(archive, destdir):
    import zipfile
    if not exists(destdir):
        os.mkdir(destdir)
    zfobj = zipfile.ZipFile(archive)
    for name in zfobj.namelist():
        if name.endswith('/'):
            os.mkdir(join(destdir, name))
        else:
            outfile = open(join(destdir, name), 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()


class Execute:
    """This is a deadlock safe version of popen2 (no stdin), that returns
    an object with errorlevel, out and err.
    """
    
    def __init__(self, command):
        outfile = tempfile.mktemp()
        errfile = tempfile.mktemp()
        self.status = os.system("( %s ) >%s 2>%s" %
                                (command, outfile, errfile)) >> 8
        self.out = open(outfile,"r").read()
        self.err = open(errfile,"r").read()
        os.remove(outfile)
        os.remove(errfile)


def acquire_lock(lock_file, max_try=10, delay=10):
    """Acquire a lock represented by a file on the file system."""
    count = 0
    while max_try <= 0 or count < max_try:
        if not exists(lock_file):
            break
        count += 1
        time.sleep(delay)
    else:
        raise Exception('Unable to acquire %s' % lock_file)
    stream = open(lock_file, 'w')
    stream.write(str(os.getpid()))
    stream.close()
    
def release_lock(lock_file):
    """Release a lock represented by a file on the file system."""
    os.remove(lock_file)


class ProgressBar(object):
    """A simple text progression bar."""
    
    def __init__(self, nbops, size=20, stream=sys.stdout):
        self._fstr = '\r[%%-%ss]' % int(size)
        self._stream = stream
        self._total = nbops
        self._size = size
        self._current = 0
        self._progress = 0

    def update(self):
        """Update the progression bar."""
        self._current += 1
        progress = int((float(self._current)/float(self._total))*self._size)
        if progress > self._progress:
            self._progress = progress
            self.refresh()

    def refresh(self):
        """Refresh the progression bar display."""
        self._stream.write(self._fstr % ('.' * min(self._progress, self._size)) )
        self._stream.flush()
