"""Deprecation utilities.

:copyright: 2006-2009 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

import sys
from warnings import warn

class class_deprecated(type):
    """metaclass to print a warning on instantiation of a deprecated class"""

    def __call__(cls, *args, **kwargs):
        msg = getattr(cls, "__deprecation_warning__",
                      "%s is deprecated" % cls.__name__)
        warn(msg, DeprecationWarning, stacklevel=2)
        return type.__call__(cls, *args, **kwargs)


def class_renamed(old_name, new_class, message=None):
    """automatically creates a class which fires a DeprecationWarning
    when instantiated.

    >>> Set = class_renamed('Set', set, 'Set is now replaced by set')
    >>> s = Set()
    sample.py:57: DeprecationWarning: Set is now replaced by set
      s = Set()
    >>>
    """
    clsdict = {}
    if message is None:
        message = '%s is deprecated, use %s' % (old_name, new_class.__name__)
    clsdict['__deprecation_warning__'] = message
    try:
        # new-style class
        return deprecated(old_name, (new_class,), clsdict)
    except (NameError, TypeError):
        # old-style class
        class DeprecatedClass(new_class):
            """FIXME: There might be a better way to handle old/new-style class
            """
            def __init__(self, *args, **kwargs):
                warn(message, DeprecationWarning, stacklevel=2)
                new_class.__init__(self, *args, **kwargs)
        return DeprecatedClass


def class_moved(new_class, old_name=None, message=None):
    """nice wrapper around class_renamed when a class has been moved into
    another module
    """
    if old_name is None:
        old_name = new_class.__name__
    if message is None:
        message = 'class %s is now available as %s.%s' % (
            old_name, new_class.__module__, new_class.__name__)
    return class_renamed(old_name, new_class, message)

def deprecated(reason=None):
    """Decorator that raises a DeprecationWarning to print a message
    when the decorated function is called.
    """
    def deprecated_decorator(func):
        message = reason or 'this function is deprecated, use %s instead'
        if '%s' in message:
            message = message % func.func_name
        def wrapped(*args, **kwargs):
            warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapped
    return deprecated_decorator

def deprecated_function(func, message=None):
    """Creates a function which fires a DeprecationWarning when used.

    For example, if <bar> is deprecated in favour of <foo>:

    >>> bar = deprecated_function(foo, 'bar is deprecated')
    >>> bar()
    sample.py:57: DeprecationWarning: bar is deprecated
      bar()
    >>>
    """
    return deprecated(message)(func)

def moved(modpath, objname):
    """use to tell that a callable has been moved to a new module.

    It returns a callable wrapper, so that when its called a warning is printed
    telling where the object can be found, import is done (and not before) and
    the actual object is called.

    NOTE: the usage is somewhat limited on classes since it will fail if the
    wrapper is use in a class ancestors list, use the `class_moved` function
    instead (which has no lazy import feature though).
    """
    def callnew(*args, **kwargs):
        from logilab.common.modutils import load_module_from_name
        message = "object %s has been moved to module %s" % (objname, modpath)
        warn(message, DeprecationWarning, stacklevel=2)
        m = load_module_from_name(modpath)
        return getattr(m, objname)(*args, **kwargs)
    return callnew

obsolete = deprecated_function(deprecated, 'obsolete is deprecated, use deprecated instead')

