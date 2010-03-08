"""Wrappers to get actually replaceable DBAPI2 compliant modules and
database connection whatever the database and client lib used.

Currently support:

- postgresql (pgdb, psycopg, psycopg2, pyPgSQL)
- mysql (MySQLdb)
- sqlite (pysqlite2, sqlite, sqlite3)

just use the `get_connection` function from this module to get a
wrapped connection.  If multiple drivers for a database are available,
you can control which one you want to use using the
`set_prefered_driver` function.

Additional helpers are also provided for advanced functionalities such
as listing existing users or databases, creating database... Get the
helper for your database using the `get_adv_func_helper` function.

:copyright: 2002-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('this module is deprecated, use logilab.db instead',
     DeprecationWarning, stacklevel=1)

from logilab.common.db import (get_connection, set_prefered_driver,
                               get_dbapi_compliant_module)
