# Copyright (c) 2002-2007 LOGILAB S.A. (Paris, FRANCE).
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
"""This modules contains wrappers to get actually replaceable DBAPI2 compliant
modules and database connection whatever the database and client lib used.

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
"""

import sys
import re
from warnings import warn

from logilab.common.deprecation import obsolete
try:
    from mx.DateTime import DateTimeType, DateTimeDeltaType, strptime
    HAS_MX_DATETIME = True
except:
    HAS_MX_DATETIME = False
    
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

    def process_value(self, value, description, encoding='utf-8', binarywrap=None):
        typecode = description[1]
        assert typecode is not None, self # dbapi module isn't supporting type codes, override to return value directly
        if typecode == self.STRING:
            if isinstance(value, str):
                return unicode(value, encoding)
        elif typecode == self.BOOLEAN:
            return bool(value)
        elif typecode == self.BINARY and not binarywrap is None:
            return binarywrap(value)
##                 elif typecode == dbapimod.DATETIME:
##                     pass
##                 elif typecode == dbapimod.NUMBER:
##                     pass
##                 else:
##                     self.warning("type -%s- unknown for %r (%s) ",
##                         typecode, value, type(value))
        return value
        
    
# Postgresql #########################################################

class _PgdbAdapter(DBAPIAdapter):
    """Simple PGDB Adapter to DBAPI (pgdb modules lacks Binary() and NUMBER)
    """
    def __init__(self, native_module, pywrap=False):
        DBAPIAdapter.__init__(self, native_module, pywrap)
        self.NUMBER = native_module.pgdbType('int2', 'int4', 'serial',
                                             'int8', 'float4', 'float8',
                                             'numeric', 'bool', 'money')
        
    def connect(self, host='', database='', user='', password='', port=''):
        """Wraps the native module connect method"""
        if port:
            warn("pgdb doesn't support 'port' parameter in connect()", UserWarning)
        kwargs = {'host' : host, 'database' : database,
                  'user' : user, 'password' : password}
        cnx = self._native_module.connect(**kwargs)
        return self._wrap_if_needed(cnx)


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
    
class _Psycopg2Adapter(_PsycopgAdapter):
    """Simple Psycopg2 Adapter to DBAPI (cnx_string differs from classical ones)
    """
    BOOLEAN = 16 # XXX see additional types in psycopg2.extensions
    def __init__(self, native_module, pywrap=False):
        DBAPIAdapter.__init__(self, native_module, pywrap)
        self._init_psycopg2()

    def _init_psycopg2(self):
        """initialize psycopg2 to use mx.DateTime for date and timestamps
        instead for datetime.datetime"""
        psycopg2 = self._native_module
        if hasattr(psycopg2, '_lc_initialized'):
            return
        psycopg2._lc_initialized = 1
        # use mxDateTime instead of datetime if available
        if HAS_MX_DATETIME:
            from psycopg2 import extensions
            extensions.register_type(psycopg2._psycopg.MXDATETIME)
            extensions.register_type(psycopg2._psycopg.MXINTERVAL)
            extensions.register_type(psycopg2._psycopg.MXDATE)
            extensions.register_type(psycopg2._psycopg.MXTIME)
            # StringIO/cStringIO adaptation
            # XXX (syt) todo, see my december discussion on the psycopg2 list
            # for a working solution
            #def adapt_stringio(stringio):
            #    print 'ADAPTING', stringio
            #    return psycopg2.Binary(stringio.getvalue())
            #import StringIO
            #extensions.register_adapter(StringIO.StringIO, adapt_stringio)
            #import cStringIO
            #extensions.register_adapter(cStringIO.StringIO, adapt_stringio)
        

class _PgsqlAdapter(DBAPIAdapter):
    """Simple pyPgSQL Adapter to DBAPI
    """
    def connect(self, host='', database='', user='', password='', port=''):
        """Handles psycopg connexion format"""
        kwargs = {'host' : host, 'port': port or None,
                  'database' : database,
                  'user' : user, 'password' : password or None}
        cnx = self._native_module.connect(**kwargs)
        return self._wrap_if_needed(cnx)


    def Binary(self, string):
        """Emulates the Binary (cf. DB-API) function"""
        return str
    
    def __getattr__(self, attrname):
        # __import__('pyPgSQL.PgSQL', ...) imports the toplevel package
        return getattr(self._native_module, attrname)


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
        if hasattr(sqlite, '_lc_initialized'):
            return
        sqlite._lc_initialized = 1

        # bytea type handling
        from StringIO import StringIO
        def adapt_bytea(data):
            return data.getvalue()
        sqlite.register_adapter(StringIO, adapt_bytea)
        def convert_bytea(data):
            return StringIO(data)
        sqlite.register_converter('bytea', convert_bytea)

        # boolean type handling
        def convert_boolean(ustr):
            if ustr.upper() in ('F', 'FALSE'):
                return False
            return True
        sqlite.register_converter('boolean', convert_boolean)
        def adapt_boolean(bval):
            return str(bval).upper()
        sqlite.register_adapter(bool, adapt_boolean)

        # date/time types handling
        if HAS_MX_DATETIME:
            def adapt_mxdatetime(mxd):
                return mxd.strftime('%Y-%m-%d %H:%M:%S')
            sqlite.register_adapter(DateTimeType, adapt_mxdatetime)
            def adapt_mxdatetimedelta(mxd):
                return mxd.strftime('%H:%M:%S')
            sqlite.register_adapter(DateTimeDeltaType, adapt_mxdatetimedelta)
            def convert_mxdate(ustr):
                return strptime(ustr, '%Y-%m-%d %H:%M:%S')
            sqlite.register_converter('date', convert_mxdate)
            def convert_mxdatetime(ustr):
                return strptime(ustr, '%Y-%m-%d %H:%M:%S')
            sqlite.register_converter('timestamp', convert_mxdatetime)
            def convert_mxtime(ustr):
                try:
                    return strptime(ustr, '%H:%M:%S')
                except:
                    # DateTime used as Time?
                    return strptime(ustr, '%Y-%m-%d %H:%M:%S')
            sqlite.register_converter('time', convert_mxtime)
        # XXX else use datetime.datetime
    
            
    def connect(self, host='', database='', user='', password='', port=None):
        """Handles sqlite connexion format"""
        sqlite = self._native_module
        
        class PySqlite2Cursor(sqlite.Cursor):
            """cursor adapting usual dict format to pysqlite named format
            in SQL queries
            """
            def _replace_parameters(self, sql, kwargs):
                if isinstance(kwargs, dict):
                    return re.sub(r'%\(([^\)]+)\)s', r':\1', sql)
                # XXX dumb
                return re.sub(r'%s', r'?', sql)
                    
            def execute(self, sql, kwargs=None):
                if kwargs is None:
                    self.__class__.__bases__[0].execute(self, sql)
                else:
                    self.__class__.__bases__[0].execute(self, self._replace_parameters(sql, kwargs), kwargs)
                    
            def executemany(self, sql, kwargss):
                if not isinstance(kwargss, (list, tuple)):
                    kwargss = tuple(kwargss)
                self.__class__.__bases__[0].executemany(self, self._replace_parameters(sql, kwargss[0]), kwargss)
                    
        class PySqlite2CnxWrapper:
            def __init__(self, cnx):
                self._cnx = cnx
                
            def cursor(self):
                return self._cnx.cursor(PySqlite2Cursor)
            
            def __getattr__(self, attrname):
                return getattr(self._cnx, attrname)
        cnx = sqlite.connect(database, detect_types=sqlite.PARSE_DECLTYPES)
        return self._wrap_if_needed(PySqlite2CnxWrapper(cnx))
    
    def process_value(self, value, description, encoding='utf-8', binarywrap=None):
        return value # no type code support, can't do anything

    
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
    BOOLEAN = 'XXX' # no specific type code for boolean
    def connect(self, host='', database='', user='', password='', port=None,
                unicode=True):
        """Handles mysqldb connexion format
        the unicode named argument asks to use Unicode objects for strings
        in result sets and query parameters
        """
        kwargs = {'host' : host or '', 'db' : database,
                  'user' : user, 'passwd' : password,
                  'use_unicode' : unicode}
        # MySQLdb doesn't support None port
        if port:
            kwargs['port'] = int(port)
        cnx = self._native_module.connect(**kwargs)
        return self._wrap_if_needed(cnx)

    def process_value(self, value, description, encoding='utf-8', binarywrap=None):
        typecode = description[1]
        # hack to differentiate mediumtext (String) and tinyblob/longblog
        # (Password/Bytes) which are all sharing the same type code :(
        if typecode == self.BINARY:
            maxsize = description[3]
            if maxsize == 16777215: # mediumtext (2**24 - 1)
                if isinstance(value, str):
                    return unicode(value, encoding)
                return value
            #if maxsize == 255: # tinyblob (2**8 - 1)
            #    return value
            if binarywrap is None:
                return value
            return binarywrap(value)
        return DBAPIAdapter.process_value(self, value, description, encoding, binarywrap)

    def type_code_test(self, cursor):
        print '*'*80
        print 'module type codes'
        for typename in ('STRING', 'BOOLEAN', 'BINARY', 'DATETIME', 'NUMBER'):
            print typename, getattr(self, typename)
        try:
            cursor.execute("""CREATE TABLE _type_code_test(
            varchar_field varchar(50),
            text_field text unicode, 
            mtext_field mediumtext,
            binary_field tinyblob,
            blob_field blob,
            lblob_field longblob
            )""")
            cursor.execute("INSERT INTO _type_code_test VALUES ('1','2','3','4', '5', '6')")
            cursor.execute("SELECT * FROM _type_code_test")
            descr = cursor.description
            print 'db fields type codes'
            for i, name in enumerate(('varchar', 'text', 'mediumtext',
                                      'binary', 'blob', 'longblob')):
                print name, descr[i]
        finally:
            cursor.execute("DROP TABLE _type_code_test")
            
## Helpers for DBMS specific advanced or non standard functionalities #########

class _GenericAdvFuncHelper:
    """Generic helper, trying to provide generic way to implement
    specific functionnalities from others DBMS

    An exception is raised when the functionality is not emulatable
    """    
    # DBMS resources descriptors and accessors
    
    users_support = True
    groups_support = True
    ilike_support = True


    TYPE_MAPPING = {
        'String' :   'text',
        'Int' :      'integer',
        'Float' :    'float',
        'Boolean' :  'boolean',
        'Date' :     'date', 
        'Time' :     'time', 
        'Datetime' : 'timestamp',
        'Interval' : 'interval',
        'Password' : 'bytea',
        'Bytes' :    'bytea',
        # FIXME: still there for use from erudi, should be moved out
        'COUNT' : 'integer',
        'MIN' :   'integer',
        'MAX' :   'integer',
        'SUM' :   'integer',
        'LOWER' : 'text',
        'UPPER' : 'text',
        }
    
    # @obsolete('use users_support attribute')
    def support_users(self):
        """return True if the DBMS support users (this is usually
        not true for in memory DBMS)
        """
        return self.users_support
    support_user = obsolete('use users_support attribute')(support_users)
    
    # @obsolete('use groups_support attribute')    
    def support_groups(self):
        """return True if the DBMS support groups"""
        return self.groups_support
    support_user = obsolete('use groups_support attribute')(support_groups)

    def system_database(self):
        """return the system database for the given driver"""
        raise NotImplementedError('not supported by this DBMS')
    
    def backup_command(self, dbname, dbhost, dbuser, dbpassword, backupfile,
                       keepownership=True):
        """return a command to backup the given database"""
        raise NotImplementedError('not supported by this DBMS')
    
    def restore_commands(self, dbname, dbhost, dbuser, backupfile,
                         encoding='utf-8', keepownership=True, drop=True):
        """return a list of commands to restore a backup the given database"""
        raise NotImplementedError('not supported by this DBMS')
    
    # helpers to standardize SQL according to the database
    
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

    def sql_temporary_table(self, table_name, table_schema,
                            drop_on_commit=True):
        return "CREATE TEMPORARY TABLE %s (%s);" % (table_name,
                                                    table_schema)
    
    def sql_drop_unique_constraint(self, table, column):
        # XXX postgres specific ?
        return 'ALTER TABLE %s DROP CONSTRAINT %s_%s_key' % (
            table, table, column)

    def boolean_value(self, value):
        if value:
            return 'TRUE'
        else:
            return 'FALSE'
        
    def increment_sequence(self, cursor, seq_name):
        for sql in self.sqls_increment_sequence(seq_name):
            cursor.execute(sql)
        return cursor.fetchone()[0]

    def create_user(self, cursor, user, password):
        """create a new database user"""
        if not self.users_support:
            raise NotImplementedError('not supported by this DBMS')
        cursor.execute("CREATE USER %(user)s "
                       "WITH PASSWORD '%(password)s'" % locals())
    
    def user_exists(self, cursor, username):
        """return True if a user with the given username exists"""
        return username in self.list_users(cursor)
    
    def list_users(self, cursor):
        """return the list of existing database users"""
        raise NotImplementedError('not supported by this DBMS')
    
    def create_database(self, cursor, dbname, owner=None, encoding='utf-8'):
        """create a new database"""
        raise NotImplementedError('not supported by this DBMS')
        
    def list_databases(self):
        """return the list of existing databases"""
        raise NotImplementedError('not supported by this DBMS')
    
    def list_tables(self, cursor):
        """return the list of tables of a database"""
        raise NotImplementedError('not supported by this DBMS')
    


def pgdbcmd(cmd, dbhost, dbuser):
    cmd = [cmd]
    if dbhost:
        cmd.append('--host=%s' % dbhost)
    if dbuser:
        cmd.append('--username=%s' % dbuser)
    return cmd


class _PGAdvFuncHelper(_GenericAdvFuncHelper):
    """Postgres helper, taking advantage of postgres SEQUENCE support
    """
    
    def system_database(self):
        """return the system database for the given driver"""
        return 'template1'
    
    def backup_command(self, dbname, dbhost, dbuser, backupfile,
                       keepownership=True):
        """return a command to backup the given database"""
        cmd = ['pg_dump -Fc']
        if dbhost:
            cmd.append('--host=%s' % dbhost)
        if dbuser:
            cmd.append('--username=%s' % dbuser)
        if not keepownership:
            cmd.append('--no-owner')
        cmd.append('--file=%s' % backupfile)
        cmd.append(dbname)
        return ' '.join(cmd)
    
    def restore_commands(self, dbname, dbhost, dbuser, backupfile,
                         encoding='utf-8', keepownership=True, drop=True):
        """return a list of commands to restore a backup the given database"""
        cmds = []
        if drop:
            cmd = pgdbcmd('dropdb', dbhost, dbuser)
            cmd.append(dbname)
            cmds.append(' '.join(cmd))
        cmd = pgdbcmd('createdb -T template0 -E %s' % encoding, dbhost, dbuser)
        cmd.append(dbname)
        cmds.append(' '.join(cmd))
        cmd = pgdbcmd('pg_restore -Fc', dbhost, dbuser)
        cmd.append('--dbname %s' % dbname)
        if not keepownership:
            cmd.append('--no-owner')
        cmd.append(backupfile)
        cmds.append(' '.join(cmd))
        return cmds
                
    def sql_create_sequence(self, seq_name):
        return 'CREATE SEQUENCE %s;' % seq_name
    
    def sql_drop_sequence(self, seq_name):
        return 'DROP SEQUENCE %s;' % seq_name
    
    def sqls_increment_sequence(self, seq_name):
        return ("SELECT nextval('%s');" % seq_name,)
    
    def sql_temporary_table(self, table_name, table_schema,
                            drop_on_commit=True):
        if not drop_on_commit:
            return "CREATE TEMPORARY TABLE %s (%s);" % (table_name,
                                                        table_schema)    
        return "CREATE TEMPORARY TABLE %s (%s) ON COMMIT DROP;" % (table_name,
                                                                   table_schema)

    def list_users(self, cursor, username=None):
        """return the list of existing database users"""
        if username:
            warn('username argument is deprecated, use user_exists method',
                 DeprecationWarning, stacklevel=2)
            return self.user_exists(cursor, username)
        cursor.execute("SELECT usename FROM pg_user")
        return [r[0] for r in cursor.fetchall()]
    
    def create_database(self, cursor, dbname, owner=None, encoding='utf-8'):
        """create a new database"""
        sql = "CREATE DATABASE %(dbname)s"
        if owner:
            sql += " WITH OWNER=%(owner)s"
        if encoding:
            sql += " ENCODING='%(encoding)s'"
        cursor.execute(sql % locals())

    def list_databases(self, cursor):
        """return the list of existing databases"""
        cursor.execute('SELECT datname FROM pg_database')
        return [r[0] for r in cursor.fetchall()]
    
    def list_tables(self, cursor):
        """return the list of tables of a database"""
        cursor.execute("SELECT tablename FROM pg_tables")
        return cursor.fetchall()

    def create_language(self, cursor, extlang):
        """postgres specific method to install a procedural language on a database"""
        # make sure plpythonu is not directly in template1
        cursor.execute("SELECT * FROM pg_language WHERE lanname='%s';" % extlang)
        if cursor.fetchall():
            print '%s language already installed' % extlang
        else:
            cursor.execute('CREATE LANGUAGE %s' % extlang)
            print '%s language installed' % extlang

            
class _SqliteAdvFuncHelper(_GenericAdvFuncHelper):
    """Generic helper, trying to provide generic way to implement
    specific functionnalities from others DBMS

    An exception is raised when the functionality is not emulatable
    """
    
    users_support = groups_support = False
    ilike_support = False
    
    
class _MyAdvFuncHelper(_GenericAdvFuncHelper):
    """Postgres helper, taking advantage of postgres SEQUENCE support
    """
    TYPE_MAPPING = _GenericAdvFuncHelper.TYPE_MAPPING.copy()
    TYPE_MAPPING['Password'] = 'tinyblob'
    TYPE_MAPPING['String'] = 'mediumtext'
    TYPE_MAPPING['Bytes'] = 'longblob'
    
    def system_database(self):
        """return the system database for the given driver"""
        return ''
    
    def backup_command(self, dbname, dbhost, dbuser, backupfile,
                       keepownership=True):
        """return a command to backup the given database"""
        # XXX compress
        return 'mysqldump -h %s -u %s -r %s %s' % (dbhost, dbuser, backupfile, dbname)
    
    def restore_commands(self, dbname, dbhost, dbuser, backupfile,
                         encoding='utf-8', keepownership=True, drop=True):
        """return a list of commands to restore a backup the given database"""
        cmds = []
        if drop:
            cmd = 'echo "DROP DATABASE %s;" | mysql -h %s -u %s' % (dbname, dbhost, dbuser)
            cmds.append(cmd)
        cmd = 'echo "%s;" | mysql -h %s -u %s' % (self.sql_create_database(dbname, encoding),
                                                  dbhost, dbuser)
        cmds.append(cmd)
        cmd = pgdbcmd('mysql -h %s -u %s < %s' % (dbname, dbhost, dbuser, backupfile))
        cmds.append(cmd)
        return cmds
                
    def sql_temporary_table(self, table_name, table_schema,
                            drop_on_commit=True):
        if not drop_on_commit:
            return "CREATE TEMPORARY TABLE %s (%s);" % (table_name,
                                                        table_schema)    
        return "CREATE TEMPORARY TABLE %s (%s) ON COMMIT DROP;" % (table_name,
                                                                   table_schema)


    def boolean_value(self, value):
        if value:
            return True
        else:
            return False
        
    def list_users(self, cursor):
        """return the list of existing database users"""
        # Host, Password
        cursor.execute("SELECT User FROM mysql.user")
        return [r[0] for r in cursor.fetchall()]

    def list_databases(self, cursor):
        """return the list of existing databases"""
        cursor.execute('SHOW DATABASES')
        return [r[0] for r in cursor.fetchall()]
    
    def sql_create_database(self, dbname, encoding='utf-8'):
        sql = "CREATE DATABASE %(dbname)s"
        if encoding:
            sql += " CHARACTER SET %(encoding)s"
        return sql % locals()
    
    def create_database(self, cursor, dbname, owner=None, encoding='utf-8'):
        """create a new database"""
        cursor.execute(self.sql_create_database(dbname, encoding))
        if owner:
            cursor.execute('GRANT ALL ON `%s`.* to %s' % (dbname, owner))
    
    def list_tables(self, cursor):
        """return the list of tables of a database"""
        cursor.execute("SHOW TABLES")
        return [r[0] for r in cursor.fetchall()]


## Drivers, Adapters and helpers registries ###################################


PREFERED_DRIVERS = {
    "postgres" : [ 'psycopg2', 'psycopg', 'pgdb', 'pyPgSQL.PgSQL', ],
    "mysql" : [ 'MySQLdb', ], # 'pyMySQL.MySQL, ],
    "sqlite" : ['sqlite3', 'pysqlite2.dbapi2', 'sqlite', ],
    }

_ADAPTERS = {
    'postgres' : { 'pgdb' : _PgdbAdapter,
                   'psycopg' : _PsycopgAdapter,
                   'psycopg2' : _Psycopg2Adapter,
                   'pyPgSQL.PgSQL' : _PgsqlAdapter,
                   },
    'mysql' : { 'MySQLdb' : _MySqlDBAdapter, },
    'sqlite' : { 'pysqlite2.dbapi2' : _PySqlite2Adapter,
                 'sqlite' : _SqliteAdapter,
                 'sqlite3' : _PySqlite2Adapter, },
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
                             'mysql': _MyAdvFuncHelper(),
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
        mod = ADAPTER_DIRECTORY.adapt(driver, prefered_drivers, pywrap=pywrap)
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
    if host and not port:
        try:
            host, port = host.split(':', 1)
        except ValueError:
            pass
    if port:
        port = int(port)
    return adapted_module.connect(host, database, user, password, port=port)
