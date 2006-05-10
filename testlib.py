
# modified copy of some functions from test/regrtest.py from PyXml

""" Copyright (c) 2003-2005 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr  

Run tests.

This will find all modules whose name match a given prefix in the test
directory, and run them.  Various command line options provide
additional facilities.

Command line options:

-v: verbose -- run tests in verbose mode with output to stdout
-q: quiet -- don't print anything except if a test fails
-t: testdir -- directory where the tests will be found
-x: exclude -- add a test to exclude
-p: profile -- profiled execution

If no non-option arguments are present, prefixes used are 'test',
'regrtest', 'smoketest' and 'unittest'.

"""
from __future__ import nested_scopes

__revision__ = "$Id: testlib.py,v 1.47 2006-04-19 10:26:15 adim Exp $"

import sys
import os
import getopt
import traceback
import unittest
import difflib
from warnings import warn

try:
    from test import test_support
except ImportError:
    # not always available
    class TestSupport:
        def unload(self, test):
            pass
    test_support = TestSupport()

from logilab.common import class_renamed, deprecated_function
from logilab.common.compat import set, enumerate
from logilab.common.modutils import load_module_from_name

__all__ = ['main', 'unittest_main', 'find_tests', 'run_test', 'spawn']

DEFAULT_PREFIXES = ('test', 'regrtest', 'smoketest', 'unittest',
                    'func', 'validation')

def main(testdir=os.getcwd()):
    """Execute a test suite.

    This also parses command-line options and modifies its behaviour
    accordingly.

    tests -- a list of strings containing test names (optional)
    testdir -- the directory in which to look for tests (optional)

    Users other than the Python test suite will certainly want to
    specify testdir; if it's omitted, the directory containing the
    Python test suite is searched for.

    If the tests argument is omitted, the tests listed on the
    command-line will be used.  If that's empty, too, then all *.py
    files beginning with test_ will be used.

    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vqx:t:p')
    except getopt.error, msg:
        print msg
        print __doc__
        return 2
    verbose = 0
    quiet = 0
    profile = 0
    exclude = []
    for o, a in opts:
        if o == '-v':
            verbose = verbose+1
        elif o == '-q':
            quiet = 1;
            verbose = 0
        elif o == '-x':
            exclude.append(a)
        elif o == '-t':
            testdir = a
        elif o == '-p':
            profile = 1
        elif o == '-h':
            print __doc__
            sys.exit(0)
            
    for i in range(len(args)):
        # Strip trailing ".py" from arguments
        if args[i][-3:] == '.py':
            args[i] = args[i][:-3]
    if exclude:
        for i in range(len(exclude)):
            # Strip trailing ".py" from arguments
            if exclude[i][-3:] == '.py':
                exclude[i] = exclude[i][:-3]
    tests = find_tests(testdir, args or DEFAULT_PREFIXES, excludes=exclude)
    sys.path.insert(0, testdir)
    # Tell tests to be moderately quiet
    test_support.verbose = verbose
    if profile:
        print >> sys.stderr, '** profiled run'
        from hotshot import Profile
        prof = Profile('stones.prof')
        good, bad, skipped, all_result = prof.runcall(run_tests, tests, quiet,
                                                      verbose)
        prof.close()
    else:
        good, bad, skipped, all_result = run_tests(tests, quiet, verbose)
    if not quiet:
        print '*'*80
        if all_result:
            print 'Ran %s test cases' % all_result.testsRun,
            if all_result.errors:
                print ', %s errors' % len(all_result.errors),
            if all_result.failures:
                print ', %s failed' % len(all_result.failures),
            if all_result.skipped:
                print ', %s skipped' % len(all_result.skipped),
            print
        if good:
            if not bad and not skipped and len(good) > 1:
                print "All",
            print _count(len(good), "test"), "OK."
        if bad:
            print _count(len(bad), "test"), "failed:",
            print ', '.join(bad)
        if skipped:
            print _count(len(skipped), "test"), "skipped:",
            print ', '.join(['%s (%s)' % (test, msg) for test, msg in skipped])
    if profile:
        from hotshot import stats
        stats = stats.load('stones.prof')
        stats.sort_stats('time', 'calls')
        stats.print_stats(30)
    sys.exit(len(bad) + len(skipped))

def run_tests(tests, quiet, verbose, runner=None):
    """ execute a list of tests
    return a 3-uple with :
       _ the list of passed tests
       _ the list of failed tests
       _ the list of skipped tests
    """
    good = []
    bad = []
    skipped = []
    all_result = None
    for test in tests:
        if not quiet:
            print 
            print '-'*80
            print "Executing", test
        result = run_test(test, verbose, runner)
        if type(result) is type(''):
            # an unexpected error occured
            skipped.append( (test, result))
        else:
            if all_result is None:
                all_result = result
            else:
                all_result.testsRun += result.testsRun
                all_result.failures += result.failures
                all_result.errors += result.errors
                all_result.skipped += result.skipped
            if result.errors or result.failures:
                bad.append(test)
                if verbose:
                    print "test", test, \
                          "failed -- %s errors, %s failures" % (
                        len(result.errors), len(result.failures))
            else:
                good.append(test)
            
    return good, bad, skipped, all_result
    
def find_tests(testdir,
               prefixes=DEFAULT_PREFIXES, suffix=".py",
               excludes=(),
               remove_suffix=1):
    """
    Return a list of all applicable test modules.
    """
    tests = []
    for name in os.listdir(testdir):
        if not suffix or name[-len(suffix):] == suffix:
            for prefix in prefixes:
                if name[:len(prefix)] == prefix:
                    if remove_suffix:
                        name = name[:-len(suffix)]
                    if name not in excludes:
                        tests.append(name)
    tests.sort()
    return tests


def run_test(test, verbose, runner=None):
    """
    Run a single test.

    test -- the name of the test
    verbose -- if true, print more messages
    """
    test_support.unload(test)
    try:
        m = load_module_from_name(test, path=sys.path)
#        m = __import__(test, globals(), locals(), sys.path)
        try:
            suite = m.suite
            if hasattr(suite, 'func_code'):
                suite = suite()
        except AttributeError:
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(m)
        if runner is None:
            runner = SkipAwareTextTestRunner()
        return runner.run(suite)
    except KeyboardInterrupt, v:
        raise KeyboardInterrupt, v, sys.exc_info()[2]
    except:
        type, value = sys.exc_info()[:2]
        msg = "test %s crashed -- %s : %s" % (test, type, value)
        if verbose:
            traceback.print_exc()
        return msg

def _count(n, word):
    """format word according to n"""
    if n == 1:
        return "%d %s" % (n, word)
    else:
        return "%d %ss" % (n, word)


## PostMortem Debug facilities #####
from pdb import Pdb
class Debugger(Pdb):
    def __init__(self, tcbk):
        Pdb.__init__(self)
        self.reset()
        while tcbk.tb_next is not None:
            tcbk = tcbk.tb_next
        self._tcbk = tcbk
        
    def start(self):
        self.interaction(self._tcbk.tb_frame, self._tcbk)

def start_interactive_mode(debuggers, descrs):
    """starts an interactive shell so that the user can inspect errors
    """
    if len(debuggers) == 1:
        # don't ask for test name if there's only one failure
        debuggers[0].start()
    else:
        while True:
            testindex = 0
            print "Choose a test to debug:"
            print "\n".join(['\t%s : %s' % (i, descr) for i, descr in enumerate(descrs)])
            print "Type 'exit' (or ^D) to quit"
            print
            try:
                todebug = raw_input('Enter a test name: ')
                if todebug.strip().lower() == 'exit':
                    print
                    break
                else:
                    try:
                        testindex = int(todebug)
                        debugger = debuggers[testindex]
                    except (ValueError, IndexError):
                        print "ERROR: invalid test number %r" % (todebug,)
                    else:
                        debugger.start()
            except (EOFError, KeyboardInterrupt):
                print
                break


# test utils ##################################################################
from cStringIO import StringIO

class SkipAwareTestResult(unittest._TextTestResult):

    def __init__(self, stream, descriptions, verbosity, exitfirst=False):
        unittest._TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.skipped = []
        self.debuggers = []
        self.descrs = []
        self.exitfirst = exitfirst

    def _create_pdb(self, test_descr):
        self.debuggers.append(Debugger(sys.exc_info()[2]))
        self.descrs.append(test_descr)
        
    def addError(self, test, err):
        exc_type, exc, tcbk = err
        # hack to avoid overriding the whole __call__ machinery in TestCase
        if exc_type == TestSkipped:
            self.addSkipped(test, exc)
        else:
            if self.exitfirst:
                self.shouldStop = True
            unittest._TextTestResult.addError(self, test, err)
        self._create_pdb(self.getDescription(test))

    def addFailure(self, test, err):
        if self.exitfirst:
            self.shouldStop = True
        unittest._TextTestResult.addFailure(self, test, err)
        self._create_pdb(self.getDescription(test))

    def addSkipped(self, test, reason):
        self.skipped.append((test, reason))
        if self.showAll:
            self.stream.writeln("SKIPPED")
        elif self.dots:
            self.stream.write('S')

    def printErrors(self):
        unittest._TextTestResult.printErrors(self)
        self.printSkippedList()
        
    def printSkippedList(self):
        for test, err in self.skipped:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % ('SKIPPED', self.getDescription(test)))
            self.stream.writeln("\t%s" % err)


class SkipAwareTextTestRunner(unittest.TextTestRunner):

    def __init__(self, verbosity=1, exitfirst=False):
        unittest.TextTestRunner.__init__(self, verbosity=verbosity)
        self.exitfirst = exitfirst

    def _makeResult(self):
        return SkipAwareTestResult(self.stream, self.descriptions,
                                   self.verbosity, self.exitfirst)


class SkipAwareTestProgram(unittest.TestProgram):
    # XXX: don't try to stay close to unittest.py, use optparse
    USAGE = """\
Usage: %(progName)s [options] [test] [...]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -i, --pdb        Enable test failure inspection
  -x, --exitfirst  Exit on first failure
  -q, --quiet      Minimal output

Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""
    def parseArgs(self, argv):
        self.pdbmode = False
        self.exitfirst = False
        import getopt
        try:
            options, args = getopt.getopt(argv[1:], 'hHvixq',
                                          ['help','verbose','quiet', 'pdb', 'exitfirst'])
            for opt, value in options:
                if opt in ('-h','-H','--help'):
                    self.usageExit()
                if opt in ('-i', '--pdb'):
                    self.pdbmode = True
                if opt in ('-x', '--exitfirst'):
                    self.exitfirst = True
                if opt in ('-q','--quiet'):
                    self.verbosity = 0
                if opt in ('-v','--verbose'):
                    self.verbosity = 2
            if len(args) == 0 and self.defaultTest is None:
                self.test = self.testLoader.loadTestsFromModule(self.module)
                return
            if len(args) > 0:
                self.testNames = args
            else:
                self.testNames = (self.defaultTest,)
            self.createTests()
        except getopt.error, msg:
            self.usageExit(msg)


    def runTests(self):
        self.testRunner = SkipAwareTextTestRunner(verbosity=self.verbosity,
                                                  exitfirst=self.exitfirst)
        result = self.testRunner.run(self.test)
        if os.environ.get('PYDEBUG'):
            warn("PYDEBUG usage is deprecated, use -i / --pdb instead", DeprecationWarning)
            self.pdbmode = True
        if result.debuggers and self.pdbmode:
            start_interactive_mode(result.debuggers, result.descrs)
        sys.exit(not result.wasSuccessful())

def unittest_main():
    """use this functon if you want to have the same functionality as unittest.main"""
    SkipAwareTestProgram()

class TestSkipped(Exception):
    """raised when a test is skipped"""
    
class TestCase(unittest.TestCase):
    """unittest.TestCase with some additional methods"""


    def defaultTestResult(self):
        return SkipAwareTestResult()

    def skip(self, msg=None):
        msg = msg or 'test was skipped'
        # warn(msg, stacklevel=2)
        raise TestSkipped(msg)
    skipped_test = deprecated_function(skip)
    
    def assertDictEquals(self, d1, d2):
        """compares two dicts

        If the two dict differ, the first difference is shown in the error
        message
        """
        d1 = d1.copy()
        for key, value in d2.items():
            try:
                if d1[key] != value:
                    self.fail('%r != %r for key %r' % (d1[key], value, key))
                del d1[key]
            except KeyError:
                self.fail('missing %r key' % key)
        if d1:
            self.fail('d2 is lacking %r' % d1)
    assertDictEqual = assertDictEquals

    def assertSetEquals(self, got, expected):
        """compares two iterables and shows difference between both"""
        got, expected = list(got), list(expected)
        self.assertEquals(len(got), len(expected))
        got, expected = set(got), set(expected)
        if got != expected:
            missing = expected - got
            unexpected = got - expected
            self.fail('\tunexepected: %s\n\tmissing: %s' % (unexpected,
                                                            missing))
    assertSetEqual = assertSetEquals

    def assertListEquals(self, l1, l2):
        """compares two lists

        If the two list differ, the first difference is shown in the error
        message
        """
        _l1 = l1[:]
        for i, value in enumerate(l2):
            try:
                if _l1[0] != value:
                    self.fail('%r != %r for index %d' % (_l1[0], value, i))
                del _l1[0]
            except IndexError:
                msg = 'l1 has only %d elements, not %s (at least %r missing)'
                self.fail(msg % (i, len(l2), value))
        if _l1:
            self.fail('l2 is lacking %r' % _l1)
    assertListEqual = assertListEquals
    
    def assertLinesEquals(self, l1, l2):
        """assert list of lines are equal"""
        self.assertListEquals(l1.splitlines(), l2.splitlines())
    assertLineEqual = assertLinesEquals

    def assertXMLWellFormed(self, stream):
        """asserts the XML stream is well-formed (no DTD conformance check)"""
        from xml.sax import make_parser, SAXParseException
        parser = make_parser()
        try:
            parser.parse(stream)
        except SAXParseException:
            self.fail('XML stream not well formed')
    assertXMLValid = deprecated_function(assertXMLWellFormed,
                                         'assertXMLValid renamed to more precise assertXMLWellFormed')

    def assertXMLStringWellFormed(self, xml_string):
        """asserts the XML string is well-formed (no DTD conformance check)"""
        stream = StringIO(xml_string)
        self.assertXMLWellFormed(stream)
        
    assertXMLStringValid = deprecated_function(
        assertXMLStringWellFormed, 'assertXMLStringValid renamed to more precise assertXMLStringWellFormed')


    def _difftext(self, lines1, lines2, junk=None):
        junk = junk or (' ', '\t')
        # result is a generator
        result = difflib.ndiff(lines1, lines2, charjunk=lambda x: x in junk)
        read = []
        for line in result:
            read.append(line)
            # lines that don't start with a ' ' are diff ones
            if not line.startswith(' '):
                self.fail(''.join(read + list(result)))
        
    def assertTextEquals(self, text1, text2, junk=None):
        """compare two multiline strings (using difflib and splitlines())"""
        self._difftext(text1.splitlines(True), text2.splitlines(True), junk)
    assertTextEqual = assertTextEquals
            
    def assertStreamEqual(self, stream1, stream2, junk=None):
        """compare two streams (using difflib and readlines())"""
        # if stream2 is stream2, readlines() on stream1 will also read lines
        # in stream2, so they'll appear different, although they're not
        if stream1 is stream2:
            return
        # make sure we compare from the beginning of the stream
        stream1.seek(0)
        stream2.seek(0)
        # ocmpare
        self._difftext(stream1.readlines(), stream2.readlines(), junk)
            
    def assertFileEqual(self, fname1, fname2, junk=(' ', '\t')):
        """compares two files using difflib"""
        self.assertStreamEqual(file(fname1), file(fname2), junk)


import doctest

class SkippedSuite(unittest.TestSuite):
    def test(self):
        """just there to trigger test execution"""
        print 'goiooo'
        self.skipped_test('doctest module has no DocTestSuite class')

class DocTest(TestCase):
    """trigger module doctest
    I don't know how to make unittest.main consider the DocTestSuite instance
    without this hack
    """
    def __call__(self, result=None):
        try:
            suite = doctest.DocTestSuite(self.module)
        except AttributeError:
            suite = SkippedSuite()
        return suite.run(result)
    run = __call__
    
    def test(self):
        """just there to trigger test execution"""

MAILBOX = None

class MockSMTP:
    """fake smtplib.SMTP"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        global MAILBOX
        self.reveived = MAILBOX = []
        
    def set_debuglevel(self, debuglevel):
        """ignore debug level"""

    def sendmail(self, fromaddr, toaddres, body):
        """push sent mail in the mailbox"""
        self.reveived.append((fromaddr, toaddres, body))

    def quit(self):
        """ignore quit"""


class MockConfigParser:
    """fake ConfigParser.ConfigParser"""
    
    def __init__(self, options):
        self.options = options
        
    def get(self, section, option):
        """return option in section"""
        return self.options[section][option]

    def has_option(self, section, option):
        """ask if option exists in section"""
        try:
            return self.get(section, option) or 1
        except KeyError:
            return 0
    

class MockConnection:
    """fake DB-API 2.0 connexion AND cursor (i.e. cursor() return self)"""
    
    def __init__(self, results):
        self.received = []
        self.states = []
        self.results = results
        
    def cursor(self):
        return self
    def execute(self, query, args=None):
        self.received.append( (query, args) )
    def fetchone(self):
        return self.results[0]
    def fetchall(self):
        return self.results
    def commit(self):
        self.states.append( ('commit', len(self.received)) )
    def rollback(self):
        self.states.append( ('rollback', len(self.received)) )
    def close(self):
        pass

MockConnexion = class_renamed('MockConnexion', MockConnection)

