# modified copy of some functions from test/regrtest.py from PyXml
"""Copyright (c) 2003-2006 LOGILAB S.A. (Paris, FRANCE).
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
-c: capture -- capture standard out/err during tests
-d: dbc     -- enable design-by-contract

If no non-option arguments are present, prefixes used are 'test',
'regrtest', 'smoketest' and 'unittest'.

"""
from __future__ import nested_scopes

import sys
import os, os.path as osp
import time
import getopt
import traceback
import unittest
import difflib
import types
from warnings import warn
from compiler.consts import CO_GENERATOR

try:
    from test import test_support
except ImportError:
    # not always available
    class TestSupport:
        def unload(self, test):
            pass
    test_support = TestSupport()

from logilab.common.deprecation import class_renamed, deprecated_function
from logilab.common.compat import set, enumerate
from logilab.common.modutils import load_module_from_name

__all__ = ['main', 'unittest_main', 'find_tests', 'run_test', 'spawn']

DEFAULT_PREFIXES = ('test', 'regrtest', 'smoketest', 'unittest',
                    'func', 'validation')

ENABLE_DBC = False

def main(testdir=None, exitafter=True):
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
        opts, args = getopt.getopt(sys.argv[1:], 'hvqx:t:pcd', ['help'])
    except getopt.error, msg:
        print msg
        print __doc__
        return 2
    verbose = 0
    quiet = False
    profile = False
    exclude = []
    capture = 0
    for o, a in opts:
        if o == '-v':
            verbose += 1
        elif o == '-q':
            quiet = True
            verbose = 0
        elif o == '-x':
            exclude.append(a)
        elif o == '-t':
            testdir = a
        elif o == '-p':
            profile = True
        elif o == '-c':
            capture += 1
        elif o == '-d':
            global ENABLE_DBC
            ENABLE_DBC = True
        elif o in ('-h', '--help'):
            print __doc__
            sys.exit(0)

    args = [item.rstrip('.py') for item in args]
    exclude = [item.rstrip('.py') for item in exclude]

    if testdir is not None:
        os.chdir(testdir)
    sys.path.insert(0, '')
    tests = find_tests('.', args or DEFAULT_PREFIXES, excludes=exclude)
    # Tell tests to be moderately quiet
    test_support.verbose = verbose
    if profile:
        print >> sys.stderr, '** profiled run'
        from hotshot import Profile
        prof = Profile('stones.prof')
        start_time, start_ctime = time.time(), time.clock()
        good, bad, skipped, all_result = prof.runcall(run_tests, tests, quiet,
                                                      verbose, None, capture)
        end_time, end_ctime = time.time(), time.clock()
        prof.close()
    else:
        start_time, start_ctime = time.time(), time.clock()
        good, bad, skipped, all_result = run_tests(tests, quiet, verbose, None, capture)
        end_time, end_ctime = time.time(), time.clock()
    if not quiet:
        print '*'*80
        if all_result:
            print 'Ran %s test cases in %0.2fs (%0.2fs CPU)' % (all_result.testsRun,
                                                                end_time - start_time,
                                                                end_ctime - start_ctime), 
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
    if exitafter:
        sys.exit(len(bad) + len(skipped))
    else:
        sys.path.pop(0)
        return len(bad)

def run_tests(tests, quiet, verbose, runner=None, capture=0):
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
        result = run_test(test, verbose, runner, capture)
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
               remove_suffix=True):
    """
    Return a list of all applicable test modules.
    """
    tests = []
    for name in os.listdir(testdir):
        if not suffix or name.endswith(suffix):
            for prefix in prefixes:
                if name.startswith(prefix):
                    if remove_suffix and name.endswith(suffix):
                        name = name[:-len(suffix)]
                    if name not in excludes:
                        tests.append(name)
    tests.sort()
    return tests


def run_test(test, verbose, runner=None, capture=0):
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
            if callable(suite):
                suite = suite()
        except AttributeError:
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(m)
        if runner is None:
            runner = SkipAwareTextTestRunner(capture=capture) # verbosity=0)
        return runner.run(suite)
    except KeyboardInterrupt, v:
        raise KeyboardInterrupt, v, sys.exc_info()[2]
    except:
        # raise
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

    def __init__(self, stream, descriptions, verbosity,
                 exitfirst=False, capture=0):
        super(SkipAwareTestResult, self).__init__(stream,
                                                  descriptions, verbosity)
        self.skipped = []
        self.debuggers = []
        self.descrs = []
        self.exitfirst = exitfirst
        self.capture = capture
        
    def _create_pdb(self, test_descr):
        self.debuggers.append(Debugger(sys.exc_info()[2]))
        self.descrs.append(test_descr)
        
    def addError(self, test, err):
        exc_type, exc, tcbk = err
        if exc_type == TestSkipped:
            self.addSkipped(test, exc)
        else:
            if self.exitfirst:
                self.shouldStop = True
            super(SkipAwareTestResult, self).addError(test, err)
            self._create_pdb(self.getDescription(test))

    def addFailure(self, test, err):
        if self.exitfirst:
            self.shouldStop = True
        super(SkipAwareTestResult, self).addError(test, err)
        self._create_pdb(self.getDescription(test))

    def addSkipped(self, test, reason):
        self.skipped.append((test, reason))
        if self.showAll:
            self.stream.writeln("SKIPPED")
        elif self.dots:
            self.stream.write('S')

    def printErrors(self):
        super(SkipAwareTestResult, self).printErrors()
        self.printSkippedList()
        
    def printSkippedList(self):
        for test, err in self.skipped:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % ('SKIPPED', self.getDescription(test)))
            self.stream.writeln("\t%s" % err)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)
            if self.capture == 1:
                output, errput = test.captured_output()
                if output:
                    self.stream.writeln(self.separator2)
                    self.stream.writeln("captured stdout".center(len(self.separator2)))
                    self.stream.writeln(self.separator2)
                    self.stream.writeln(output)
                else:
                    self.stream.writeln('no stdout'.center(len(self.separator2)))
                if errput:
                    self.stream.writeln(self.separator2)
                    self.stream.writeln("captured stderr".center(len(self.separator2)))
                    self.stream.writeln(self.separator2)
                    self.stream.writeln(errput)
                else:
                    self.stream.writeln('no stderr'.center(len(self.separator2)))


class SkipAwareTextTestRunner(unittest.TextTestRunner):

    def __init__(self, stream=sys.stderr, verbosity=1,
                 exitfirst=False, capture=False):
        super(SkipAwareTextTestRunner, self).__init__(stream=stream,
                                                      verbosity=verbosity)
        self.exitfirst = exitfirst
        self.capture = capture
        
    def _makeResult(self):
        return SkipAwareTestResult(self.stream, self.descriptions, self.verbosity,
                                   self.exitfirst, self.capture)


class keywords(dict):
    """keyword args (**kwargs) support for generative tests"""

class starargs(tuple):
    """variable arguments (*args) for generative tests"""
    def __new__(cls, *args):
        return tuple.__new__(cls, args)



class NonStrictTestLoader(unittest.TestLoader):
    """
    overrides default testloader to be able to omit classname when
    specifying tests to run on command line. For example, if the file
    test_foo.py contains ::
    
        class FooTC(TestCase):
            def test_foo1(self): # ...
            def test_foo2(self): # ...
            def test_bar1(self): # ...

        class BarTC(TestCase):
            def test_bar2(self): # ...

    python test_foo.py will run the 3 tests in FooTC
    python test_foo.py FooTC will run the 3 tests in FooTC
    python test_foo.py test_foo will run test_foo1 and test_foo2
    python test_foo.py test_foo1 will run test_foo1
    python test_foo.py test_bar will run FooTC.test_bar1 and BarTC.test_bar2
    """
    def loadTestsFromNames(self, names, module=None):
        suites = []
        for name in names:
            suites.extend(self.loadTestsFromName(name, module))
        return self.suiteClass(suites)


    def _collect_tests(self, module):
        tests = {}
        for obj in vars(module).values():
            if issubclass(type(obj), (types.ClassType, type)) and \
                   issubclass(obj, unittest.TestCase):
                classname = obj.__name__
                methodnames = []
                # obj is a TestCase class
                for attrname in dir(obj):
                    if attrname.startswith(self.testMethodPrefix):
                        attr = getattr(obj, attrname)
                        if callable(attr):
                            methodnames.append(attrname)
                # keep track of class (obj) for convenience
                tests[classname] = (obj, methodnames)
        return tests
        
    def loadTestsFromName(self, name, module=None):
        parts = name.split('.')
        if module is None or len(parts) > 2:
            # let the base class do its job here
            return [super(NonStrictTestLoader, self).loadTestsFromName(name)]
        tests = self._collect_tests(module)
        # import pprint
        # pprint.pprint(tests)
        collected = []
        if len(parts) == 1:
            pattern = parts[0]
            if pattern in tests:
                # case python unittest_foo.py MyTestTC
                klass, methodnames = tests[pattern]
                for methodname in methodnames:
                    collected = [klass(methodname) for methodname in methodnames]
            else:
                # case python unittest_foo.py something
                for klass, methodnames in tests.values():
                    collected += [klass(methodname) for methodname in methodnames
                                  if self._test_should_be_collected(methodname, pattern)]
        elif len(parts) == 2:
            # case "MyClass.test_1"
            classname, pattern = parts
            klass, methodnames = tests.get(classname, (None, []))
            for methodname in methodnames:
                collected = [klass(methodname) for methodname in methodnames
                             if self._test_should_be_collected(methodname, pattern)]
        return collected

    def _test_should_be_collected(self, methodname, pattern):
        """returns True if <methodname> matches <pattern>
        >>> self._test_should_be_collected('test_foobar', 'foo')
        True
        >>> self._test_should_be_collected('testfoobar', 'foo')
        True
        >>> self._test_should_be_collected('test_foobar', 'test_foo')
        True
        >>> self._test_should_be_collected('test_foobar', 'testfoo')
        False
        """
        return pattern in methodname

class SkipAwareTestProgram(unittest.TestProgram):
    # XXX: don't try to stay close to unittest.py, use optparse
    USAGE = """\
Usage: %(progName)s [options] [test] [...]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -i, --pdb        Enable test failure inspection
  -x, --exitfirst  Exit on first failure
  -c, --capture    Captures and prints standard out/err only on errors
  -q, --quiet      Minimal output

Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""
    def __init__(self, module='__main__'):
        super(SkipAwareTestProgram, self).__init__(
            module=module, testLoader=NonStrictTestLoader())
       
    
    def parseArgs(self, argv):
        self.pdbmode = False
        self.exitfirst = False
        self.capture = 0
        import getopt
        try:
            options, args = getopt.getopt(argv[1:], 'hHvixqc',
                                          ['help','verbose','quiet', 'pdb', 'exitfirst', 'capture'])
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
                if opt in ('-c', '--capture'):
                    self.capture += 1
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
                                                  exitfirst=self.exitfirst,
                                                  capture=self.capture)
        result = self.testRunner.run(self.test)
        if os.environ.get('PYDEBUG'):
            warn("PYDEBUG usage is deprecated, use -i / --pdb instead", DeprecationWarning)
            self.pdbmode = True
        if result.debuggers and self.pdbmode:
            start_interactive_mode(result.debuggers, result.descrs)
        sys.exit(not result.wasSuccessful())




class FDCapture: 
    """adapted from py lib (http://codespeak.net/py)
    Capture IO to/from a given os-level filedescriptor.
    """
    def __init__(self, fd, attr='stdout'):
        self.targetfd = fd
        self.tmpfile = os.tmpfile() # self.maketempfile()
        # save original file descriptor
        self._savefd = os.dup(fd)
        # override original file descriptor
        os.dup2(self.tmpfile.fileno(), fd)
        # also modify sys module directly
        self.oldval = getattr(sys, attr)
        setattr(sys, attr, self.tmpfile)
        self.attr = attr
    
##     def maketempfile(self):
##         tmpf = os.tmpfile()
##         fd = os.dup(tmpf.fileno())
##         newf = os.fdopen(fd, tmpf.mode, 0) # No buffering
##         tmpf.close()
##         return newf
        
    def restore(self):
        """restore original fd and returns captured output"""
        # hack hack hack
        self.tmpfile.flush()
        try:
            ref_file = getattr(sys, '__%s__' % self.attr)
            ref_file.flush()
        except AttributeError:
            pass
        if hasattr(self.oldval, 'flush'):
            self.oldval.flush()
        # restore original file descriptor
        os.dup2(self._savefd, self.targetfd)
        # restore sys module
        setattr(sys, self.attr, self.oldval)
        # close backup descriptor
        os.close(self._savefd)
        # go to beginning of file and read it
        self.tmpfile.seek(0)
        return self.tmpfile.read()


def _capture(which='stdout'):
    """private method, should not be called directly
    (cf. capture_stdout() and capture_stderr())
    """
    assert which in ('stdout', 'stderr'), "Can only capture stdout or stderr, not %s" % which
    if which == 'stdout':
        fd = 1
    else:
        fd = 2
    return FDCapture(fd, which)
    
def capture_stdout():
    """captures the standard output

    returns a handle object which has a `restore()` method.
    The restore() method returns the captured stdout and restores it
    """
    return _capture('stdout')
        
def capture_stderr():
    """captures the standard error output

    returns a handle object which has a `restore()` method.
    The restore() method returns the captured stderr and restores it
    """
    return _capture('stderr')


def unittest_main(module='__main__'):
    """use this functon if you want to have the same functionality
    as unittest.main"""
    SkipAwareTestProgram(module)

class TestSkipped(Exception):
    """raised when a test is skipped"""

def is_generator(function):
    flags = function.func_code.co_flags
    return flags & CO_GENERATOR


def parse_generative_args(params):
    args = []
    varargs = ()
    kwargs = {}
    flags = 0 # 2 <=> starargs, 4 <=> kwargs
    for param in params:
        if isinstance(param, starargs):
            varargs = param
            if flags:
                raise TypeError('found starargs after keywords !')
            flags |= 2
            args += list(varargs)
        elif isinstance(param, keywords):
            kwargs = param
            if flags & 4:
                raise TypeError('got multiple keywords parameters')
            flags |= 4
        elif flags & 2 or flags & 4:
            raise TypeError('found parameters after kwargs or args')
        else:
            args.append(param)

    return args, kwargs

class TestCase(unittest.TestCase):
    """unittest.TestCase with some additional methods"""

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        # internal API changed in python2.5
        if sys.version_info >= (2, 5):
            self.__exc_info = self._exc_info
            self.__testMethodName = self._testMethodName
        self._captured_stdout = ""
        self._captured_stderr = ""
            
    def captured_output(self):
        return self._captured_stdout, self._captured_stderr

    def _start_capture(self):
        if self.capture:
            self._out, self._err = capture_stdout(), capture_stderr()

    def _stop_capture(self):
        if self.capture:
            out, err = self._out.restore(), self._err.restore()
            self._captured_stdout += out
            self._captured_stderr += err


    def quiet_run(self, result, func, *args, **kwargs):
        self._start_capture()
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            self._stop_capture()
            raise
        except:
            self._stop_capture()
            result.addError(self, self.__exc_info())
            return False
        self._stop_capture()
        return True

    def __call__(self, result=None):
        """rewrite TestCase.__call__ to support generative tests
        This is mostly a copy/paste from unittest.py (i.e same
        variable names, same logic, except for the generative tests part)
        """
        if result is None:
            result = self.defaultTestResult()
        self.capture = getattr(result, 'capture', False)
        result.startTest(self)
        testMethod = getattr(self, self.__testMethodName)
        try:
            if not self.quiet_run(result, self.setUp):
                return
            # generative tests
            if is_generator(testMethod.im_func):
                success = self._proceed_generative(result, testMethod)
            else:
                status = self._proceed(result, testMethod)
                success = (status == 0)
            if not self.quiet_run(result, self.tearDown):
                return
            if success:
                result.addSuccess(self)
        finally:
            result.stopTest(self)


            
    def _proceed_generative(self, result, testfunc, args=()):
        # cancel startTest()'s increment
        result.testsRun -= 1
        try:
            for params in testfunc():
                if not isinstance(params, (tuple, list)):
                    params = (params,)
                func = params[0]
                args, kwargs = parse_generative_args(params[1:])
                # increment test counter manually
                result.testsRun += 1
                status = self._proceed(result, func, args, kwargs)
                if status == 0:
                    result.addSuccess(self)
                    success = True
                else:
                    success = False
                    if status == 2:
                        result.shouldStop = True
                if result.shouldStop: # either on error or on exitfirst + error
                    break
        except:
            # if an error occurs between two yield
            result.addError(self, self.__exc_info())
            success = False
        return success

    def _proceed(self, result, testfunc, args=(), kwargs=None):
        """proceed the actual test
        returns 0 on success, 1 on failure, 2 on error

        Note: addSuccess can't be called here because we have to wait
        for tearDown to be successfully executed to declare the test as
        successful
        """
        self._start_capture()
        kwargs = kwargs or {}
        try:
            testfunc(*args, **kwargs)
            self._stop_capture()
        except self.failureException:
            self._stop_capture()
            result.addFailure(self, self.__exc_info())
            return 1
        except KeyboardInterrupt:
            self._stop_capture()
            raise
        except:
            self._stop_capture()
            result.addError(self, self.__exc_info())
            return 2
        return 0
            
    def defaultTestResult(self):
        return SkipAwareTestResult()

    def skip(self, msg=None):
        msg = msg or 'test was skipped'
        raise TestSkipped(msg)
    skipped_test = deprecated_function(skip)
    
    def assertDictEquals(self, d1, d2):
        """compares two dicts

        If the two dict differ, the first difference is shown in the error
        message
        """
        d1 = d1.copy()
        msgs = []
        for key, value in d2.items():
            try:
                if d1[key] != value:
                    msgs.append('%r != %r for key %r' % (d1[key], value, key))
                del d1[key]
            except KeyError:
                msgs.append('missing %r key' % key)
        if d1:
            msgs.append('d2 is lacking %r' % d1)
        if msgs:
            self.fail('\n'.join(msgs))
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
                    from pprint import pprint
                    pprint(l1)
                    pprint(l2)
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
            
    def assertIsInstance(self, obj, klass, msg=None):
        """compares two files using difflib"""
        if msg is None:
            msg = '%s is not an instance of %s' % (obj, klass)
        self.assert_(isinstance(obj, klass), msg)


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

def mock_object(**params):
    """creates an object using params to set attributes
    >>> option = mock_object(verbose=False, index=range(5))
    >>> option.verbose
    False
    >>> option.index
    [0, 1, 2, 3, 4]
    """
    return type('Mock', (), params)()


def create_files(paths, chroot):
    """creates directories and files found in <path>

    :param path: list of relative paths to files or directories
    :param chroot: the root directory in which paths will be created

    >>> from os.path import isdir, isfile
    >>> isdir('/tmp/a')
    False
    >>> create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], '/tmp')
    >>> isdir('/tmp/a')
    True
    >>> isdir('/tmp/a/b/c')
    True
    >>> isfile('/tmp/a/b/c/d/e.py')
    True 
    >>> isfile('/tmp/a/b/foo.py')
    True
    """
    dirs, files = set(), set()
    for path in paths:
        path = osp.join(chroot, path)
        filename = osp.basename(path)
        # path is a directory path
        if filename == '':
            dirs.add(path)
        # path is a filename path
        else:
            dirs.add(osp.dirname(path))
            files.add(path)
    for dirpath in dirs:
        if not osp.isdir(dirpath):
            os.makedirs(dirpath)
    for filepath in files:
        file(filepath, 'w').close()

def enable_dbc(*args):
    """
    Without arguments, return True if contracts can be enabled and should be
    enabled (see option -d), return False otherwise.

    With arguments, return False if contracts can't or shouldn't be enabled,
    otherwise weave ContractAspect with items passed as arguments.
    """
    if not ENABLE_DBC:
        return False
    try:
        from logilab.aspects.weaver import weaver
        from logilab.aspects.lib.contracts import ContractAspect
    except ImportError:
        sys.stderr.write('Warning: logilab.aspects is not available. Contracts disabled.')
        return False
    for arg in args:
        weaver.weave_module(arg, ContractAspect)
    return True

    
class AttrObject: # XXX cf mock_object
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
