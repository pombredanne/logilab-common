"""Log utilities.

:copyright: 2000-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses

# FIXME using logging instead
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('logservice module is deprecated and will disappear in a near release. \
use logging module instead.',
     DeprecationWarning, stacklevel=2)

from logilab.common.logger import make_logger, LOG_ERR, LOG_WARN, LOG_NOTICE, \
     LOG_INFO, LOG_CRIT, LOG_DEBUG

def init_log(treshold, method='eprint', sid='common-log-service',
             logger=None, output=None):
    """init the logging system and and log methods to builtins"""
    if logger is None:
        logger = make_logger(method, treshold, sid, output=output)
    # add log functions and constants to builtins
    __builtins__.update({'log': logger.log,
                         'log_traceback' : logger.log_traceback,
                         'LOG_CRIT':   LOG_CRIT,
                         'LOG_ERR':    LOG_ERR,
                         'LOG_WARN':   LOG_WARN,
                         'LOG_NOTICE': LOG_NOTICE,
                         'LOG_INFO' :  LOG_INFO,
                         'LOG_DEBUG':  LOG_DEBUG,
                         })

init_log(LOG_ERR)


