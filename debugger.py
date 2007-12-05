"""customized version of pdb's default debugger.

- sets up a history file
- uses ipython if available to colorize lines of code
- overrides list command to search for current block instead
  of using 5 lines of context
"""

try:
    import readline
except ImportError:
    readline = None
import os
import os.path as osp
import sys
from pdb import Pdb
from cStringIO import StringIO
import inspect

try:
    from IPython import PyColorize
except ImportError:
    def colorize(source, *args):
        """fallback colorize function"""
        return source
else:
    def colorize(source, start_lineno, curlineno):
        """"""
        parser = PyColorize.Parser()
        output = StringIO()
        parser.format(source, output)
        annotated = []
        for index, line in enumerate(output.getvalue().splitlines()):
            lineno = index + start_lineno
            if lineno == curlineno:
                annotated.append('%4s\t->\t%s' % (lineno, line))
            else:
                annotated.append('%4s\t\t%s' % (lineno, line))                
        return '\n'.join(annotated)

def getsource(obj):
    """Return the text of the source code for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a single string.  An
    IOError is raised if the source code cannot be retrieved."""
    lines, lnum = inspect.getsourcelines(obj)
    return ''.join(lines), lnum


################################################################
class Debugger(Pdb):
    """custom debugger
    
    - sets up a history file
    - uses ipython if available to colorize lines of code
    - overrides list command to search for current block instead
      of using 5 lines of context
    """
    def __init__(self, tcbk):
        Pdb.__init__(self)
        self.reset()
        while tcbk.tb_next is not None:
            tcbk = tcbk.tb_next
        self._tcbk = tcbk
        self._histfile = osp.join(os.environ["HOME"], ".pdbhist")
        
    def setup_history_file(self):
        """if readline is available, read pdb history file
        """
        if readline is not None:
            try:
                readline.read_history_file(self._histfile)
            except IOError:
                pass

    def start(self):
        """starts the interactive mode"""
        self.interaction(self._tcbk.tb_frame, self._tcbk)

    def setup(self, frame, tcbk):
        """setup hook: set up history file"""
        self.setup_history_file()
        Pdb.setup(self, frame, tcbk)

    def set_quit(self):
        """quit hook: save commands in the history file"""
        if readline is not None:
            readline.write_history_file(self._histfile)
        Pdb.set_quit(self)


#     def getvariables(self):
#         frame = self.curframe
#         if frame:
#             print '=======>', frame.f_globals.keys() + frame.f_globals.keys()
#             return frame.f_globals.keys() + frame.f_globals.keys()
#         return []
       
#     def completenames(self, text, *ignored):
#         basenames = Pdb.completenames(text, *ignored)
#         return sorted(basenames + self.getvariables)

#     ## completion
#     def complete(self, text, state):
#         """Return the next possible completion for 'text'.

#         If a command has not been entered, then complete against command list.
#         Otherwise try to call complete_<command> to get list of completions.
#         """
#         print '===> completing', text, state
#         xxx = Pdb.complete(self, text, state)
#         print 'got', xxx
#         return xxx
        
        
    ## specific / overidden commands 
    def do_list(self, arg):
        """overrides default list command to display the surrounding block
        instead of 5 lines of context
        """
        self.lastcmd = 'list'
        if not arg:
            try:
                source, start_lineno = getsource(self.curframe)
                print colorize(''.join(source), start_lineno,
                               self.curframe.f_lineno)
            except KeyboardInterrupt:
                pass
        else:
            Pdb.do_list(self, arg)
    do_l = do_list
        


def pm():
    """use our custom debugger"""
    dbg = Debugger(sys.last_traceback)
    dbg.start()

