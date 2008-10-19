"""functions to manipulate ast tuples.

:copyright: 2003-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"
__author__ = u"Sylvain Thenault"

from warnings import warn
warn('this module has been moved into logilab.astng and will disappear from \
logilab.common in a future release',
     DeprecationWarning, stacklevel=1)

import symbol
import token
from types import TupleType

def debuild(ast_tuple):
    """
    reverse ast_tuple to string
    """
    if type(ast_tuple[1]) is TupleType:
        result = ''
        for child in ast_tuple[1:]: 
            result = '%s%s' % (result, debuild(child))
        return result
    else:
        return ast_tuple[1]

def clean(ast_tuple):
    """
    reverse ast tuple to a list of tokens
    merge sequences (token.NAME, token.DOT, token.NAME)
    """
    result = []
    last = None
    for couple in _clean(ast_tuple):
        if couple[0] == token.NAME and last == token.DOT:
            result[-1][1] += couple[1]
        elif couple[0] == token.DOT and last == token.NAME:
            result[-1][1] += couple[1]
        else:
            result.append(couple)
        last = couple[0]
    return result

def _clean(ast_tuple):
    """ transform the ast into as list of tokens (i.e. final elements)
    """
    if type(ast_tuple[1]) is TupleType:
        v = []
        for c in ast_tuple[1:]:
            v += _clean(c)
        return v
    else:
        return [list(ast_tuple[:2])]
    
def cvrtr(tuple):
    """debug method returning an ast string in a readable fashion"""
    if type(tuple) is TupleType:
        try:
            try:
                txt = 'token.'+token.tok_name[tuple[0]]
            except:
                txt = 'symbol.'+symbol.sym_name[tuple[0]]
        except:
            txt =  'Unknown token/symbol'
        return [txt] + map(cvrtr, tuple[1:])
    else:
        return tuple

__all__ = ('debuild', 'clean', 'cvrtr')
