import os.path as osp

try:
    from mercurial.error import RepoError
    from mercurial.__version__ import version as hg_version
except ImportError:
    from mercurial.repo import RepoError
    from mercurial.version import get_version
    hg_version = get_version()

from mercurial.hg import repository as Repository
from mercurial.ui import ui as Ui
from mercurial.node import short
try:
    # mercurial >= 1.2 (?)
    from mercurial.cmdutil import walkchangerevs
except ImportError, ex:
    from mercurial.commands import walkchangerevs
try:
    # mercurial >= 1.1 (.1?)
    from mercurial.util import cachefunc
except ImportError, ex:
    def cachefunc(func):
        return func
try:
    # mercurial >= 1.3.1
    from mercurial import encoding
    _encoding = encoding.encoding
except ImportError:
    try:
        from mercurial.util import _encoding
    except ImportError:
        import locale
        # stay compatible with mercurial 0.9.1 (etch debian release)
        # (borrowed from mercurial.util 1.1.2)
        try:
            _encoding = os.environ.get("HGENCODING")
            if sys.platform == 'darwin' and not _encoding:
                # On darwin, getpreferredencoding ignores the locale environment and
                # always returns mac-roman. We override this if the environment is
                # not C (has been customized by the user).
                locale.setlocale(locale.LC_CTYPE, '')
                _encoding = locale.getlocale()[1]
            if not _encoding:
                _encoding = locale.getpreferredencoding() or 'ascii'
        except locale.Error:
            _encoding = 'ascii'
try:
    # demandimport causes problems when activated, ensure it isn't
    # XXX put this in apycot where the pb has been noticed?
    from mercurial import demandimport
    demandimport.disable()
except:
    pass

Ui.warn = lambda *args, **kwargs: 0 # make it quiet

def find_repository(path):
    """returns <path>'s mercurial repository

    None if <path> is not under hg control
    """
    path = osp.realpath(osp.abspath(path))
    while not osp.isdir(osp.join(path, ".hg")):
        oldpath = path
        path = osp.dirname(path)
        if path == oldpath:
            return None
    return path


def get_repository(path):
    """Simple function that open a hg repository"""
    repopath = find_repository(path)
    if repopath is None:
        raise RuntimeError('no repository found in %s' % osp.abspath(path))
    return Repository(Ui(), path=repopath)
