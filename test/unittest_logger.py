"""unittests for logilab.common.logger"""

from tempfile import mktemp
import os
import sys
from cStringIO import StringIO

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.logger import *


def get_logged_messages(output):
    """strip timestamps and extract effective logged text
    (log lines look like: [timestamp] message)
    """
    return [line.split(']')[-1].strip() for line in output.splitlines()]


class LoggerTC(TestCase):

    def test_defaultlogging(self):
        # redirect stdout so that we can test
        stdout_backup = sys.stdout
        sys.stdout = StringIO()
        # make default logger
        logger = make_logger()
        logger.log(message='hello')
        logger.log(message='world')
        output = sys.stdout.getvalue()
        msg = get_logged_messages(output)
        # restore stdout
        sys.stdout = stdout_backup
        self.assertEquals(msg, ['hello', 'world'])

    def test_filelogging(self):
        filename = mktemp(dir='/tmp')
        # make file logger
        logger = make_logger(method='file', output=filename)
        logger.log(message='hello')
        logger.log(message='world')
        # make sure everything gets flushed (testing purpose)
        logger.output.flush()
        output = open(filename).read() #os.read(descr, 300)
        # close everything correcly
        #os.close(descr)
        logger.output.close()
        # remove file
        os.remove(filename)
        self.assertEquals(get_logged_messages(output), ['hello', 'world'])

if __name__ == '__main__':
    unittest_main()

