"""Define a logger interface and two concrete loggers: one which prints
everything on stdout, the other using syslog.

:copyright: 2000-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses

# FIXME use logging from stdlib instead.
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('logilab.common.logger module is deprecated and will disappear in a future release. \
use logging module instead.',
     DeprecationWarning, stacklevel=2)

import sys
import traceback
import time


LOG_EMERG   = 0
LOG_ALERT   = 1
LOG_CRIT    = 2
LOG_ERR     = 3
LOG_WARN    = 4
LOG_NOTICE  = 5
LOG_INFO    = 6
LOG_DEBUG   = 7

INDICATORS = ['emergency', 'alert', 'critical', 'error',
              'warning', 'notice', 'info', 'debug']


def make_logger(method='print', threshold=LOG_DEBUG, sid=None, output=None):
    """return a logger for the given method
    
    known methods are 'print', 'eprint' and syslog'
    """
    if method == 'print':
        if output is None:
            output = sys.stdout
        return PrintLogger(threshold, output, sid=sid)
    elif method == 'eprint':
        return PrintLogger(threshold, sys.stderr, sid=sid)
    elif method == 'syslog':
        return SysLogger(threshold, sid)
    elif method == 'file':
        if not output:
            raise ValueError('No logfile specified')
        else:
            logfile = open(output, 'a')
            return PrintLogger(threshold, logfile, sid=sid)
    else:
        raise ValueError('Unknown logger method: %r' % method)


class AbstractLogger:
    """logger interface.
    Priorities allow to filter on the importance of events
    An event gets logged if it's priority is lower than the threshold"""

    def __init__(self, threshold=LOG_DEBUG, priority_indicator=1):
        self.threshold = threshold
        self.priority_indicator = priority_indicator
        
    def log(self, priority=LOG_DEBUG, message='', substs=None):
        """log a message with priority <priority>
        substs are optional substrings
        """
        #print 'LOG', self, priority, self.threshold, message
        if priority <= self.threshold :
            if substs is not None:
                message = message % substs
            if self.priority_indicator:
                message = '[%s] %s' % (INDICATORS[priority], message)
            self._writelog(priority, message)

    def _writelog(self, priority, message):
        """Override this method in concrete class """
        raise NotImplementedError()

    def log_traceback(self, priority=LOG_ERR, tb_info=None):
        """log traceback information with priority <priority>
        """
        assert tb_info is not None
        e_type, value, tbck = tb_info
        stacktb = traceback.extract_tb(tbck)
        l = ['Traceback (most recent call last):']
        for stackentry in stacktb :
            if stackentry[3]:
                plus = '\n    %s' % stackentry[3]
            else:
                plus = ''
            l.append('filename="%s" line_number="%s" function_name="%s"%s' %
                     (stackentry[0], stackentry[1], stackentry[2], plus))
        try:
            l.append(str(e_type) + ': ' + value.__str__())
        except UnicodeError:
            l.append(str(e_type) + ' (message can\'t be displayed)')
            
        self.log(priority, '\n'.join(l))


class PrintLogger(AbstractLogger):
    """logger implementation

    log everything to a file, using the standard output by default
    """
    
    def __init__(self, threshold, output=sys.stdout, sid=None,
                 encoding='UTF-8'):
        AbstractLogger.__init__(self, threshold)
        self.output = output
        self.sid = sid
        self.encoding = encoding
        
    def _writelog(self, priority, message):
        """overridden from AbstractLogger"""
        if isinstance(message, unicode):
            message = message.encode(self.encoding, 'replace')
        if self.sid is not None:
            self.output.write('[%s] [%s] %s\n' % (time.asctime(), self.sid,
                                                  message))
        else:
            self.output.write('[%s] %s\n' % (time.asctime(), message))
        self.output.flush()

class SysLogger(AbstractLogger):
    """ logger implementation

    log everything to syslog daemon
    use the LOCAL_7 facility
    """

    def __init__(self, threshold, sid=None, encoding='UTF-8'):
        import syslog
        AbstractLogger.__init__(self, threshold)
        if sid is None:
            sid = 'syslog'
        self.encoding = encoding
        syslog.openlog(sid, syslog.LOG_PID)
        
    def _writelog(self, priority, message):
        """overridden from AbstractLogger"""
        import syslog
        if isinstance(message, unicode):
            message = message.encode(self.encoding, 'replace')
        syslog.syslog(priority | syslog.LOG_LOCAL7, message)

