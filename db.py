# Copyright (c) 2002-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""Helpers to get a DBAPI2 compliant database connection.
"""

__revision__ = "$Id: db.py,v 1.35 2006-04-25 12:02:09 syt Exp $"

import sys
import re

__all__ = ['get_dbapi_compliant_module', 
           'get_connection', 'set_prefered_driver',
           'PyConnection', 'PyCursor',
           'UnknownDriver', 'NoAdapterFound',
           ]

class UnknownDriver(Exception):
    """raised when a unknown driver is given to get connexion"""

class NoAdapterFound(Exception):
    """Raised when no Adpater to DBAPI was found"""
    def __init__(self, obj, objname=None, protocol='DBAPI'):
        if objname is None:
            objname = obj.__name__
        Exception.__init__(self, "Could not adapt %s to protocol %s" %
                           (objname, protocol))
        self.adapted_obj = obj
        self.objname = objname
        self._protocol = protocol


def _import_driver_module(driver, drivers, imported_elements=None, quiet=True):
    """Imports the first module found in 'drivers' for 'driver'

    :rtype: tuple
    :returns: the tuple module_object, module_name where module_object
              is the dbapi module, and modname the module's name
    """
    if not driver in drivers:
        raise UnknownDriver(driver)
    imported_elements = imported_elements or []
    for modname in drivers[driver]:
        try:
            if not quiet:
                print >> sys.stderr, 'Trying %s' % modname
            module = __import__(modname, globals(), locals(), imported_elements)
            break
        except ImportError:
            if not quiet:
                print >> sys.stderr, '%s is not available' % modname
            continue
    else:
        raise ImportError('Unable to import a %s module' % driver)
    if not imported_elements:
        for part in modname.split('.')[1:]:
            module = getattr(module, part)
    return module, modname


## Connection and cursor wrappers #############################################
        
class PyConnection:
    """A simple connection wrapper in python (useful for profiling)"""
    def __init__(self, cnx):
        """Wraps the original connection object"""
        self._cnx = cnx

    # XXX : Would it work if only __getattr__ was defined 
    def cursor(self):
        """Wraps cursor()"""
        return PyCursor(self._cnx.cursor())

    def commit(self):
        """Wraps commit()"""
        return self._cnx.commit()

    def rollback(self):
        """Wraps rollback()"""
        return self._cnx.rollback()

    def close(self):
        """Wraps close()"""
        return self._cnx.close()

    def __getattr__(self, attrname):
        return getattr(self._cnx, attrname)    


class PyCursor:
    """A simple cursor wrapper in python (useful for profiling)"""
    def __init__(self, cursor):
        self._cursor = cursor

    def close(self):
        """Wraps close()"""
        return self._cursor.close()
        
    def execute(self, *args, **kwargs):
        """Wraps execute()"""
        return self._cursor.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        """Wraps executemany()"""
        return self._cursor.executemany(*args, **kwargs)

    def fetchone(self, *args, **kwargs):
        """Wraps fetchone()"""
        return self._cursor.fetchone(*args, **kwargs)

    def fetchmany(self, *args, **kwargs):
        """Wraps execute()"""
        return self._cursor.fetchmany(*args, **kwargs)

    def fetchall(self, *args, **kwargs):
        """Wraps fetchall()"""
        return self._cursor.fetchall(*args, **kwargs)

    def __getattr__(self, attrname):
        return getattr(self._cursor, attrname)
    

## Adapters list ##############################################################
    
class DBAPIAdapter:
    """Base class for all DBAPI adpaters"""

    def __init__(self, native_module, pywrap=False):
        """
        :type native_module: module
        :param native_module: the database's driver adapted module
        """
        self._native_module = native_module
        self._pywrap = pywrap

    def connect(self, host='', database='', user='', password='', port=''):
        """Wraps the native module connect method"""
        kwargs = {'host' : host, 'port' : port, 'database' : database,
                  'user' : user, 'password' : password}
        cnx = self._native_module.connect(**kwargs)
        return self._wrap_if_needed(cnx)

    def _wrap_if_needed(self, cnx):
        """Wraps the connection object if self._pywrap is True, and returns it
        If false, returns the original cnx object
        """
        if self._pywrap:
            return PyConnection(cnx)
        else:
            return cnx
    
    def __getattr__(self, attrname):
        return getattr(self._native_module, attrname)


# Postgresql #########################################################

class _PgdbAdapter(DBAPIAdapter):
    """Simple PGDB Adapter to DBAPI (pgdb modules lacks Binary() and NUMBER)
    """
    def __init__(self, native_module, pywrap=False):
        DBAPIAdapter.__init__(self, native_module, pywrap)
        self.NUMBER = native_module.pgdbType('int2', 'int4', 'serial',
                                             'int8', 'float4', 'float8',
                                             'numeric', 'bool', 'money')
        

class _PsycopgAdapter(DBAPIAdapter):
    """Simple Psycopg Adapter to DBAPI (cnx_string differs from classical ones)
    """
    def connect(self, host='', database='', user='', password='', port=''):
        """Handles psycopg connexion format"""
        if host:
            cnx_string = 'host=%s  dbname=%s  user=%s' % (host, database, user)
        else:
            cnx_string = 'dbname=%s  user=%s' % (database, user)
        if port:
            cnx_string += ' port=%s' % port
        if password:
            cnx_string = '%s password=%s' % (cnx_string, password)
        cnx = self._native_module.connect(cnx_string)
        cnx.set_isolation_level(1)
        return self._wrap_if_needed(cnx)
    


class _PgsqlAdapter(DBAPIAdapter):
    """Simple pyPgSQL Adapter to DBAPI
    """
    def connect(self, host='', database='', user='', password=''):
        """Handles psycopg connexion format"""
        kwargs = {'host' : host, 'port': port, 'database' : database,
                  'user' : user, 'password' : password or None}
        cnx = self._native_module.connect(**kwargs)
        return self._wrap_if_needed(cnx)


    def Binary(self, string):
        """Emulates the Binary (cf. DB-API) function"""
        return str
    
    def __getattr__(self, attrname):
        # __import__('pyPgSQL.PgSQL', ...) imports the toplevel package
        return getattr(self._native_module.PgSQL, attrname)


# Sqlite #############################################################

class _PySqlite2Adapter(DBAPIAdapter):
    """Simple pysqlite2 Adapter to DBAPI
    """
    def __init__(self, native_module, pywrap=False):
        DBAPIAdapter.__init__(self, native_module, pywrap)
        self._init_pysqlite2()
        # no type code in pysqlite2
        self.BINARY = 'XXX'
        self.STRING = 'XXX'
        self.DATETIME = 'XXX'
        self.NUMBER = 'XXX'

    def _init_pysqlite2(self):
        """initialize pysqlite2 to use mx.DateTime for date and timestamps"""
        sqlite = self._native_module
        if hasattr(sqlite, '_mx_initialized'):
            return

        from mx.DateTime import DateTimeType, strptime

        def adapt_mxdatetime(mxd):
            return mxd.strftime('%F %H:%M:%S')
        sqlite.register_adapter(DateTimeType, adapt_mxdatetime)

        def convert_mxdate(ustr):
            return strptime(ustr, '%F %H:%M:%S')
        sqlite.register_converter('date', convert_mxdate)

        def convert_mxdatetime(ustr):
            return strptime(ustr, '%F %H:%M:%S')
        sqlite.register_converter('timestamp', convert_mxdatetime)

        def convert_boolean(ustr):
            if ustr.lower() == 'false':
                return False
            return True
        sqlite.register_converter('boolean', convert_boolean)

        sqlite._mx_initialized = 1

            
    def connect(self, host='', database='', user='', password='', port=None):
        """Handles sqlite connexion format"""
        sqlite = self._native_module
        
        class PySqlite2Cursor(sqlite.Cursor):
            """cursor adapting usual dict format to pysqlite named format
            in SQL queries
            """
            def execute(self, sql, kwargs=None):
                if kwargs is not None:
                    sql = re.sub(r'%\(([^\)]+)\)s', r':\1', sql)
                    self.__class__.__bases__[0].execute(self, sql, kwargs)
                else:
                    self.__class__.__bases__[0].execute(self, sql)
                    
        class PySqlite2CnxWrapper:
            def __init__(self, cnx):
                self._cnx = cnx
                
            def cursor(self):
                return self._cnx.cursor(PySqlite2Cursor)
            
            def __getattr__(self, attrname):
                return getattr(self._cnx, attrname)

        cnx = sqlite.connect(database, detect_types=sqlite.PARSE_DECLTYPES)
        return self._wrap_if_needed(PySqlite2CnxWrapper(cnx))

    
class _SqliteAdapter(DBAPIAdapter):
    """Simple sqlite Adapter to DBAPI
    """
    def __init__(self, native_module, pywrap=False):
        DBAPIAdapter.__init__(self, native_module, pywrap)
        self.DATETIME = native_module.TIMESTAMP
        
    def connect(self, host='', database='', user='', password='', port=''):
        """Handles sqlite connexion format"""
        cnx = self._native_module.connect(database)
        return self._wrap_if_needed(cnx)


# Mysql ##############################################################

class _MySqlDBAdapter(DBAPIAdapter):
    """Simple mysql Adapter to DBAPI
    """
    def connect(self, host='', database='', user='', password='', port='',
                unicode=False):
        """Handles mysqldb connexion format
        the unicode named argument asks to use Unicode objects for strings
        in result sets and query parameters
        """
        kwargs = {'host' : host, 'port' : port, 'db' : database,
                  'user' : user, 'passwd' : password or None,
                  'use_unicode' : unicode}
        return self._native_module.connect(**kwargs)


## Helpers for DBMS specific Advanced functionalities #########################

class _GenericAdvFuncHelper:
    """Generic helper, trying to provide generic way to implement
    specific functionnalities from others DBMS

    An exception is raised when the functionality is not emulatable
    """
    
    def support_users(self):
        """return True if the DBMS support users (this is usually
        not true for in memory DBMS)
        """
        return True
    
    def support_groups(self):
        """return True if the DBMS support groups"""
        return True

    def system_database(self):
        """return the system database for the given driver"""
        raise Exception('not supported by this DBMS')

    def sql_current_date(self):
        return 'CURRENT_DATE'
    
    def sql_current_time(self):
        return 'CURRENT_TIME'
    
    def sql_current_timestamp(self):
        return 'CURRENT_TIMESTAMP'
    
    def sql_create_sequence(self, seq_name):
        return '''CREATE TABLE %s (last INTEGER);
INSERT INTO %s VALUES (0);''' % (seq_name, seq_name)
    
    def sql_drop_sequence(self, seq_name):
        return 'DROP TABLE %s;' % seq_name
    
    def sqls_increment_sequence(self, seq_name):
        return ('UPDATE %s SET last=last+1;' % seq_name,
                'SELECT last FROM %s;' % seq_name)

    def increment_sequence(self, cursor, seq_name):
        for sql in self.sqls_increment_sequence(seq_name):
            cursor.execute(sql)
        return cursor.fetchone()[0]

    
class _PGAdvFuncHelper(_GenericAdvFuncHelper):
    """Postgres helper, taking advantage of postgres SEQUENCE support
    """
    
    def system_database(self):
        """return the system database for the given driver"""
        return 'template1'

    def sql_create_sequence(self, seq_name):
        return 'CREATE SEQUENCE %s;' % seq_name
    
    def sql_drop_sequence(self, seq_name):
        return 'DROP SEQUENCE %s;' % seq_name
    
    def sqls_increment_sequence(self, seq_name):
        return ("SELECT nextval('%s');" % seq_name,)


class _SqliteAdvFuncHelper(_GenericAdvFuncHelper):
    """Generic helper, trying to provide generic way to implement
    specific functionnalities from others DBMS

    An exception is raised when the functionality is not emulatable
    """
    
    def support_users(self):
        """return True if the DBMS support users (this is usually
        not true for in memory DBMS)
        """
        return False
    
    def support_groups(self):
        """return True if the DBMS support groups"""
        return False
    
    def sql_current_date(self):
        return "DATE('now')"
    
    def sql_current_time(self):
        return "TIME('now')"
    
    def sql_current_timestamp(self):
        return "DATETIME('now')"
    

## Drivers, Adapters and helpers registries ###################################


PREFERED_DRIVERS = {
    "postgres" : [ 'psycopg', 'pgdb', 'pyPgSQL.PgSQL', ],
    "mysql" : [ 'MySQLdb', ], # 'pyMySQL.MySQL, ],
    "sqlite" : [ 'pysqlite2.dbapi2', 'sqlite', ],
    }

_ADAPTERS = {
    'postgres' : { 'pgdb' : _PgdbAdapter,
                   'psycopg' : _PsycopgAdapter,
                   'pyPgSQL.PgSQL' : _PgsqlAdapter,
                   },
    'mysql' : { 'MySQLdb' : _MySqlDBAdapter, },
    'sqlite' : { 'pysqlite2.dbapi2' : _PySqlite2Adapter,
                 'sqlite' : _SqliteAdapter, },
    }

# _AdapterDirectory could be more generic by adding a 'protocol' parameter
# This one would become an adapter for 'DBAPI' protocol
class _AdapterDirectory(dict):
    """A simple dict that registers all adapters"""
    def register_adapter(self, adapter, driver, modname):
        """Registers 'adapter' in directory as adapting 'mod'"""
        try:
            driver_dict = self[driver]
        except KeyError:
            self[driver] = {}
            
        # XXX Should we have a list of adapters ?
        driver_dict[modname] = adapter
    
    def adapt(self, database, prefered_drivers = None, pywrap = False):
        """Returns an dbapi-compliant object based for database"""
        prefered_drivers = prefered_drivers or PREFERED_DRIVERS
        module, modname = _import_driver_module(database, prefered_drivers)
        try:
            return self[database][modname](module, pywrap=pywrap)
        except KeyError:
            raise NoAdapterFound(obj=module)        

    def get_adapter(self, database, modname):
        try:
            return self[database][modname]
        except KeyError:
            raise NoAdapterFound(None, modname)

ADAPTER_DIRECTORY = _AdapterDirectory(_ADAPTERS)
del _AdapterDirectory
    
ADV_FUNC_HELPER_DIRECTORY = {'postgres': _PGAdvFuncHelper(),
                             'sqlite': _SqliteAdvFuncHelper(),
                             None: _GenericAdvFuncHelper()}


## Main functions #############################################################
    
def set_prefered_driver(database, module, _drivers=PREFERED_DRIVERS):
    """sets the prefered driver module for database
    database is the name of the db engine (postgresql, mysql...)
    module is the name of the module providing the connect function
    syntax is (params_func, post_process_func_or_None)
    _drivers is a optionnal dictionnary of drivers
    """
    try:
        modules = _drivers[database]
    except KeyError:
        raise UnknownDriver('Unknown database %s' % database)
    # Remove module from modules list, and re-insert it in first position
    try:
        modules.remove(module)
    except ValueError:
        raise UnknownDriver('Unknown module %s for %s' % (module, database))
    modules.insert(0, module)

def get_adv_func_helper(driver):
    """returns an advanced function helper for the given driver"""
    return ADV_FUNC_HELPER_DIRECTORY.get(driver,
                                         ADV_FUNC_HELPER_DIRECTORY[None])
    
def get_dbapi_compliant_module(driver, prefered_drivers = None, quiet = False,
                               pywrap = False):
    """returns a fully dbapi compliant module"""
    try:
        mod = ADAPTER_DIRECTORY.adapt(driver, prefered_drivers, pywrap = pywrap)
    except NoAdapterFound, err:
        if not quiet:
            msg = 'No Adapter found for %s, returning native module'
            print >> sys.stderr, msg % err.objname
        mod = err.adapted_obj
    mod.adv_func_helper = get_adv_func_helper(driver)
    return mod

def get_connection(driver='postgres', host='', database='', user='', 
                  password='', port='', quiet=False, drivers=PREFERED_DRIVERS,
                  pywrap=False):
    """return a db connexion according to given arguments"""
    module, modname = _import_driver_module(driver, drivers, ['connect'])
    try:
        adapter = ADAPTER_DIRECTORY.get_adapter(driver, modname)
    except NoAdapterFound, err:
        if not quiet:
            msg = 'No Adapter found for %s, using default one' % err.objname
            print >> sys.stderr, msg
        adapted_module = DBAPIAdapter(module, pywrap)
    else:
        adapted_module = adapter(module, pywrap)
    if not port:
        try:
            host, port = host.split(':', 1)
        except ValueError:
            pass
    if port:
        port = int(port)
    return adapted_module.connect(host, database, user, password, port=port)
