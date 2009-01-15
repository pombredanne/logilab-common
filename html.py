"""Print traceback in HTML.

:copyright: 2000-2008 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('html module is deprecated and will disappear in a near release',
     DeprecationWarning, stacklevel=2)

import traceback
from xml.sax.saxutils import escape  

# mk html traceback error #####################################################

def html_traceback(info, exception,
                   title='', encoding='ISO-8859-1', body=''):
    """Return an html formatted traceback from python exception infos.
    """
    #typ, value, tbck = info
    stacktb = traceback.extract_tb(info[2]) #tbck)
    strings = []
    if body:
        strings.append('<div class="error_body">')
        strings.append(body)
        strings.append('</div>')
    if title:
        strings.append('<h1 class="error">%s</h1>'% escape(title))
    strings.append('<p class="error">%s</p>' % escape(str(exception)))
    strings.append('<div class="error_traceback">')
    for stackentry in stacktb :
        strings.append('<b>File</b> <b class="file">%s</b>, <b>line</b> '
                      '<b class="line">%s</b>, <b>function</b> '
                      '<b class="function">%s</b>:<br/>'%(
            escape(stackentry[0]), stackentry[1], stackentry[2]))
        if stackentry[3]:
            string = escape(repr(stackentry[3])[1:-1])#.encode(encoding)
            strings.append('&nbsp;&nbsp;%s<br/>\n' % string)
    strings.append('</div>')
    return '\n'.join(strings)
