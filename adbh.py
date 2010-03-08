"""Helpers for DBMS specific (advanced or non standard) functionalities.

Helpers are provided for postgresql, mysql and sqlite.

:copyright:
  2000-2010 `LOGILAB S.A. <http://www.logilab.fr>`_ (Paris, FRANCE),
  all rights reserved.

:contact:
  http://www.logilab.org/project/logilab-common --
  mailto:python-projects@logilab.org

:license:
  `General Public License version 2
  <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>`_
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('this module is deprecated, use logilab.db instead',
     DeprecationWarning, stacklevel=1)

from logilab.db import FunctionDescr, get_db_helper as get_adv_func_helper
