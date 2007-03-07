"""
unit tests for module logilab.common.db

"""
__revision__ = "$Id: unittest_db.py,v 1.13 2006-03-13 12:42:56 syt Exp $"

import socket

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.db import *
from logilab.common.db import PREFERED_DRIVERS, _GenericAdvFuncHelper, _PGAdvFuncHelper


class PreferedDriverTC(TestCase):
    def setUp(self):
        self.drivers = {"pg":[('foo', None), ('bar', None)]}
        self.drivers = {'pg' : ["foo", "bar"]}
        
    def testNormal(self):
        set_prefered_driver('pg','bar', self.drivers)
        self.assertEquals('bar', self.drivers['pg'][0])
    
    def testFailuresDb(self):
        try:
            set_prefered_driver('oracle','bar', self.drivers)
            self.fail()
        except UnknownDriver, exc:
            self.assertEquals(exc.args[0], 'Unknown database oracle')

    def testFailuresDriver(self):
        try:
            set_prefered_driver('pg','baz', self.drivers)
            self.fail()
        except UnknownDriver, exc:
            self.assertEquals(exc.args[0], 'Unknown module baz for pg')

    def testGlobalVar(self):
        # XXX: Is this test supposed to be useful ? Is it supposed to test
        #      set_prefered_driver ?
        old_drivers = PREFERED_DRIVERS['postgres'][:]
        expected = old_drivers[:]
        expected.insert(0, expected.pop(expected.index('pgdb')))
        set_prefered_driver('postgres', 'pgdb')
        self.assertEquals(PREFERED_DRIVERS['postgres'], expected)
        set_prefered_driver('postgres', 'psycopg')
        # self.assertEquals(PREFERED_DRIVERS['postgres'], old_drivers)
        expected.insert(0, expected.pop(expected.index('psycopg')))
        self.assertEquals(PREFERED_DRIVERS['postgres'], expected)


class GetCnxTC(TestCase):
    def setUp(self):
        if not socket.gethostname().startswith('lepus'):
            self.skip("those tests require specific DB configuration")
        self.host = None # 'crater.logilab.fr'
        self.db = 'template1'
        self.user = 'adim'
        self.passwd = 'adim'
        
    def testPsyco(self):
        set_prefered_driver('postgres', 'psycopg')
        try:
            cnx = get_connection('postgres',
                                 self.host, self.db, self.user, self.passwd,
                                 quiet=1)
        except ImportError:
            self.skip('python-psycopg is not installed')

    def testPgdb(self):
        set_prefered_driver('postgres', 'pgdb')
        try:
            cnx = get_connection('postgres',
                                 self.host, self.db, self.user, self.passwd,
                                 quiet=1)
        except ImportError:
            self.skip('python-pgsql is not installed')

    def testPgsql(self):
        set_prefered_driver('postgres', 'pyPgSQL.PgSQL')
        try:
            cnx = get_connection('postgres',
                                 self.host, self.db, self.user, self.passwd,
                                 quiet=1)
        except ImportError:
            self.skip('python-pygresql is not installed')

    def testMysql(self):
        set_prefered_driver('mysql', 'MySQLdb')
        try:
            cnx = get_connection('mysql', self.host, database='', user='root',
                                 quiet=1)
        except ImportError:
            self.skip('python-mysqldb is not installed')
        except Exception, ex:
            # no mysql running ?
            import MySQLdb
            if not (isinstance(ex, MySQLdb.OperationalError) and ex.args[0] == 2003):
                raise

    def test_connection_wrap(self):
        """Tests the connection wrapping"""
        try:
            cnx = get_connection('postgres',
                                 self.host, self.db, self.user, self.passwd,
                                 quiet=1)
        except ImportError:
            self.skip('postgresql dbapi module not installed')
        self.failIf(isinstance(cnx, PyConnection),
                    'cnx should *not* be a PyConnection instance')
        cnx = get_connection('postgres',
                             self.host, self.db, self.user, self.passwd,
                             quiet=1, pywrap = True)
        self.failUnless(isinstance(cnx, PyConnection),
                        'cnx should be a PyConnection instance')
        

    def test_cursor_wrap(self):
        """Tests cursor wrapping"""
        try:
            cnx = get_connection('postgres',
                                 self.host, self.db, self.user, self.passwd,
                                 quiet=1, pywrap = True)
        except ImportError:
            self.skip('postgresql dbapi module not installed')
        cursor = cnx.cursor()
        self.failUnless(isinstance(cursor, PyCursor),
                        'cnx should be a PyCursor instance')


class DBAPIAdaptersTC(TestCase):
    """Tests DbApi adapters management"""

    def setUp(self):
        """Memorize original PREFERED_DRIVERS"""
        self.old_drivers = PREFERED_DRIVERS['postgres'][:]
        self.host = 'crater.logilab.fr'
        self.db = 'gincotest2'
        self.user = 'adim'
        self.passwd = 'adim'

    def tearDown(self):
        """Reset PREFERED_DRIVERS as it was"""
        PREFERED_DRIVERS['postgres'] = self.old_drivers

    def test_raise(self):
        self.assertRaises(UnknownDriver, get_dbapi_compliant_module, 'pougloup')
        
    def test_pgdb_types(self):
        """Tests that NUMBER really wraps all number types"""
        PREFERED_DRIVERS['postgres'] = ['pgdb']
        #set_prefered_driver('postgres', 'pgdb')
        try:
            module = get_dbapi_compliant_module('postgres')
        except ImportError:
            self.skip('postgresql pgdb module not installed')
        number_types = ('int2', 'int4', 'serial', 
                        'int8', 'float4', 'float8', 
                        'numeric', 'bool', 'money')
        for num_type in number_types:
            yield self.assertEquals, num_type, module.NUMBER
        yield self.assertNotEquals, 'char', module.NUMBER

    def test_pypgsql_getattr(self):
        """Tests the getattr() delegation for pyPgSQL"""
        set_prefered_driver('postgres', 'pyPgSQL.PgSQL')
        try:
            module = get_dbapi_compliant_module('postgres')
        except ImportError:
            self.skip('postgresql dbapi module not installed')            
        try:
            binary = module.BINARY
        except AttributeError, err:
            raise
            self.fail(str(err))        

    def test_adv_func_helper(self):
        try:
            module = get_dbapi_compliant_module('postgres')
        except ImportError:
            self.skip('postgresql dbapi module not installed')            
        self.failUnless(isinstance(module.adv_func_helper, _PGAdvFuncHelper))
        module = get_dbapi_compliant_module('sqlite')
        self.failUnless(isinstance(module.adv_func_helper, _GenericAdvFuncHelper))


if __name__ == '__main__':
    unittest_main()
