"""%prog [OPTIONS] [testfile [testpattern]]

examples:

pytest path/to/mytests.py
pytest path/to/mytests.py TheseTests
pytest path/to/mytests.py TheseTests.test_thisone

pytest one (will run both test_thisone and test_thatone)
pytest path/to/mytests.py -s not (will skip test_notthisone)
"""

import os, sys
import os.path as osp
from time import time, clock

from logilab.common.fileutils import abspath_listdir
from logilab.common import testlib
import doctest
import unittest

# monkeypatch unittest and doctest (ouch !)
unittest.TestCase = testlib.TestCase
unittest.main = testlib.unittest_main
unittest._TextTestResult = testlib.SkipAwareTestResult
unittest.TextTestRunner = testlib.SkipAwareTextTestRunner
unittest.TestLoader = testlib.NonStrictTestLoader
unittest.TestProgram = testlib.SkipAwareTestProgram
if sys.version_info >= (2, 4):
    doctest.DocTestCase.__bases__ = (testlib.TestCase,)
else:
    unittest.FunctionTestCase.__bases__ = (testlib.TestCase,)

def autopath(projdir=os.getcwd()):
    """try to find project's root and add it to sys.path"""
    curdir = osp.abspath(projdir)
    while osp.isfile(osp.join(curdir, '__init__.py')):
        newdir = osp.normpath(osp.join(curdir, os.pardir))
        if newdir == curdir:
            break
        curdir = newdir
    else:
        sys.path.insert(0, curdir)
    sys.path.insert(0, '')

class GlobalTestReport(object):
    """this class holds global test statistics"""
    def __init__(self):
        self.ran = 0
        self.skipped = 0
        self.failures = 0
        self.errors = 0
        self.ttime = 0
        self.ctime = 0
        self.modulescount = 0
        self.errmodules = []

    def feed(self, filename, testresult, ttime, ctime):
        """integrates new test information into internal statistics"""
        ran = testresult.testsRun
        self.ran += ran
        self.skipped += len(getattr(testresult, 'skipped', ()))
        self.failures += len(testresult.failures)
        self.errors += len(testresult.errors)
        self.ttime += ttime
        self.ctime += ctime
        self.modulescount += 1
        if not testresult.wasSuccessful():
            problems = len(testresult.failures) + len(testresult.errors)
            self.errmodules.append((filename[:-3], problems, ran))
    
    def __str__(self):
        """this is just presentation stuff"""
        line1 = ['Ran %s test cases in %.2fs (%.2fs CPU)'
                 % (self.ran, self.ttime, self.ctime)]
        if self.errors:
            line1.append('%s errors' % self.errors)
        if self.failures:
            line1.append('%s failures' % self.failures)
        if self.skipped:
            line1.append('%s skipped' % self.skipped)
        modulesok = self.modulescount - len(self.errmodules)
        if self.errors or self.failures:
            line2 = '%s modules OK (%s failed)' % (modulesok,
                                                   len(self.errmodules))
            descr = ', '.join(['%s [%s/%s]' % info for info in self.errmodules])
            line3 = '\nfailures: %s' % descr
        else:
            line2 = 'All %s modules OK' % modulesok
            line3 = ''
        return '%s\n%s%s' % (', '.join(line1), line2, line3)


def this_is_a_testfile(filename):
    """returns True if `filename` seems to be a test file"""
    filename = osp.basename(filename)
    return ((filename.startswith('unittest') or filename.startswith('test')) 
            and filename.endswith('.py'))
    
def testall(exitfirst=False):
    """walks trhough current working directory, finds something
    which can be considered as a testdir and runs every test there
    """
    errcode = 0
    for dirname, dirs, files in os.walk(os.getcwd()):
        for skipped in ('CVS', '.svn', '.hg'):
            if skipped in dirs:
                dirs.remove(skipped)
        basename = osp.basename(dirname)
        if basename in ('test', 'tests'):
            # we found a testdir, let's explore it !
            errcode += testonedir(dirname, exitfirst)
    return errcode


def testonedir(testdir, exitfirst=False, report=None):
    """finds each testfile in the `testdir` and runs it"""
    report = report or GlobalTestReport()
    for filename in abspath_listdir(testdir):
        if this_is_a_testfile(filename):
            # run test and collect information
            prog, ttime, ctime = testfile(filename, batchmode=True)
            report.feed(filename, prog.result, ttime, ctime)
            if exitfirst and not prog.result.wasSuccessful():
                break
    # everything has been ran, print report
    print "*" * 79
    print report
    return report.failures + report.errors


def testfile(filename, batchmode=False):
    """runs every test in `filename`
    
    :param filename: an absolute path pointing to a unittest file
    """
    here = os.getcwd()
    dirname = osp.dirname(filename)
    if dirname:
        os.chdir(dirname)
    modname = osp.basename(filename)[:-3]
    print ('  %s  ' % osp.basename(filename)).center(70, '=')
    try:
        tstart, cstart = time(), clock()
        testprog = testlib.unittest_main(modname, batchmode=batchmode)
        tend, cend = time(), clock()
        return testprog, (tend - tstart), (cend - cstart)
    finally:
        if dirname:
            os.chdir(here)
        

def parseargs():
    """Parse the command line and return (options processed), (options to pass to
    unittest_main()), (explicitfile or None).
    """
    from optparse import OptionParser
    parser = OptionParser(usage=__doc__)

    newargs = []
    def rebuild_cmdline(option, opt, value, parser):
        """carry the option to unittest_main"""
        newargs.append(opt)

    def rebuild_and_store(option, opt, value, parser):
        """carry the option to unittest_main and store
        the value on current parser
        """
        newargs.append(opt)
        setattr(parser.values, option.dest, True)

    # pytest options
    parser.add_option('-t', dest='testdir', default=None,
                      help="directory where the tests will be found")
    parser.add_option('-d', dest='dbc', default=False,
                      action="store_true", help="enable design-by-contract")
    # unittest_main options provided and passed through pytest
    parser.add_option('-v', '--verbose', callback=rebuild_cmdline,
                      action="callback", help="Verbose output")
    parser.add_option('-i', '--pdb', callback=rebuild_cmdline,
                      action="callback", help="Enable test failure inspection")
    parser.add_option('-x', '--exitfirst', callback=rebuild_and_store,
                      dest="exitfirst",
                      action="callback", help="Exit on first failure "
                      "(only make sense when pytest run one test file)")
    parser.add_option('-c', '--capture', callback=rebuild_cmdline,
                      action="callback", 
                      help="Captures and prints standard out/err only on errors "
                      "(only make sense when pytest run one test file)")
    parser.add_option('-p', '--printonly',
                      # XXX: I wish I could use the callback action but it
                      #      doesn't seem to be able to get the value
                      #      associated to the option
                      action="store", dest="printonly", default=None,
                      help="Only prints lines matching specified pattern (implies capture) "
                      "(only make sense when pytest run one test file)")
    parser.add_option('-s', '--skip',
                      # XXX: I wish I could use the callback action but it
                      #      doesn't seem to be able to get the value
                      #      associated to the option
                      action="store", dest="skipped", default=None,
                      help="test names matching this name will be skipped "
                      "to skip several patterns, use commas")
    parser.add_option('-q', '--quiet', callback=rebuild_cmdline,
                      action="callback", help="Minimal output")

    # parse the command line
    options, args = parser.parse_args()
    filenames = [arg for arg in args if arg.endswith('.py')]
    if filenames:
        if len(filenames) > 1:
            parser.error("only one filename is acceptable")
        explicitfile = filenames[0]
        args.remove(explicitfile)
    else:
        explicitfile = None
    # someone wants DBC
    testlib.ENABLE_DBC = options.dbc
    if options.printonly:
        newargs.extend(['--printonly', options.printonly])
    if options.skipped:
        newargs.extend(['--skip', options.skipped])
    # append additional args to the new sys.argv and let unittest_main
    # do the rest
    newargs += args
    return options, newargs, explicitfile 
    
def run():
    autopath()
    options, newargs, explicitfile = parseargs()
    # mock a new command line
    sys.argv[1:] = newargs
    if explicitfile:
        sys.exit(testfile(explicitfile))
    elif options.testdir:
        sys.exit(testonedir(options.testdir, options.exitfirst))
    else:
        sys.exit(testall(options.exitfirst))
