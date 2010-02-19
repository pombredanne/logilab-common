"""
Wrapper around Pyodbc to alleviate bad perf issue when using sqlserver
in multithreaded mode.

:copyright: 2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
:contact: http://www.logilab.fr/ -- mailto:contact@logilab.fr
:license: General Public License version 2 - http://www.gnu.org/licenses
"""

## Communication protocol:

## command len\n
## len bytes (pickled data)

## commands:
## NEW (classname, args, kwargs) -> object id
## CALL (obj id, method, args, kwargs) -> (VAL length\n return value)
##                                        (REF 0 object_id\n)
##                                        (EXC length\n exception)
##                                        (NONE 0)
## DEL (object id)

import sys
import subprocess
from cPickle import dumps, loads, HIGHEST_PROTOCOL
import struct # if we need binary protocol
from exceptions import *

if sys.platform == 'win32':
    #pylint:disable-msg=F0401
    import pyodbc as dbapimodule
    from pyodbc import *
    import pyodbc
else:
    import psycopg2 as dbapimodule
    from psycopg2 import *
    from psycopg2 import _psycopg

class ProtocolError(OperationalError):
    pass


def connect(*args, **kwargs):
    return ConnectionProxy._new_connection(*args, **kwargs)


class Binary(object):
    def __init__(self, value):
        self.value = value[:]


class Proxy(object):
    remote_class = None # Provide remote class name, None means _new will fail
    def __init__(self, obj_id, pipe):
        self._id = obj_id
        self._pipe = pipe


    def _call(self, method, args=None, kwargs=None, proxy_class=None):
        try:
            _in = self._pipe.stdout
            _out = self._pipe.stdin
            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}
            data = dumps((self._id, method, args, kwargs), HIGHEST_PROTOCOL)
            length = len(data)
            _out.write('CALL %d\r\n' % length)
            _out.write(data)
            _out.flush()
            raw_answer = _in.readline()
            if raw_answer == '':
                raise ProtocolError('connection lost while waiting answer '
                                    'to CALL %s %s %s %s' % (self._id,
                                                             method,
                                                             args,
                                                             kwargs))
            answer_head = raw_answer.strip().split()
            if answer_head[0] not in ('REF', 'VAL', 'EXC', 'NONE'):
                head = ' '.join(answer_head)
                raise ProtocolError('Unknown answer header [%r]' % head)
            length = int(answer_head[1])
            if answer_head[0] == 'REF':
                if proxy_class is None:
                    raise ProtocolError('unexpected REF message')
                obj_id = int(answer_head[2])
                return proxy_class(obj_id, self._pipe)
            elif answer_head[0] == 'NONE':
                return None
            else:
                data = _in.read(length)
                value = loads(data)
                if answer_head[0] == 'VAL':
                    return value
                else: # 'EXC':
                    exc_class_name, args = value
                    exc = globals()[exc_class_name](*args)
                    raise exc
        except IOError, exc:
            raise ProtocolError('IOError %s' % exc)

    @classmethod
    def _new(cls, pipe, args, kwargs):
        if cls.remote_class is None:
            raise TypeError('%s is note remotely instanciable' % cls.__name__)
        try:
            data = dumps((cls.remote_class, args, kwargs), HIGHEST_PROTOCOL)
            length = len(data)
            pipe.stdin.write('NEW %d\r\n' % length)
            pipe.stdin.write(data)
            pipe.stdin.flush()
            raw_answer = pipe.stdout.readline()
            if raw_answer == '':
                raise ProtocolError('connection lost while waiting answer '
                                    'to NEW %s %s %s' % (cls.remote_class,
                                                         args,
                                                         kwargs))
            answer_head = raw_answer.strip().split()
            if answer_head[0] not in ('REF', 'EXC'):
                head = ' '.join(answer_head)
                raise ProtocolError('Unknown answer header [%r]' % head)
            length = int(answer_head[1])
            if answer_head[0] == 'REF':
                obj_id = int(answer_head[2])
                return cls(obj_id, pipe)
            else: # exception
                data = pipe.stdout.read(length)
                value = loads(data)
                exc_class_name, args = value
                exc = globals()[exc_class_name](*args)
                raise exc
        except IOError, exc:
            raise ProtocolError('IOError %s' % exc)

    def __del__(self):
        data = dumps(self._id, HIGHEST_PROTOCOL)
        try:
            self._pipe.stdin.write('DEL %d\r\n' % len(data))
            self._pipe.stdin.write(data)
            self._pipe.stdin.flush()
        except IOError:
            pass

    def __getattr__(self, name):
        return self._call('__getattr__', (name,))

class ConnectionProxy(Proxy):
    remote_class = 'RemoteConnection'
    @classmethod
    def _new_connection(cls, *args, **kwargs):
        cmd = [sys.executable, '-u', __file__]
        pipe = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=sys.stderr)
        return cls._new(pipe, args, kwargs)

    def cursor(self):
        return self._call('cursor', proxy_class=CursorProxy)

    def close(self):
        self._call('close')

    def commit(self):
        self._call('commit')

    def rollback(self):
        self._call('rollback')

    #pycopg2 specific
    def set_isolation_level(self, *args, **kwargs):
        self._call('set_isolation_level', args, kwargs)


class CursorProxy(Proxy):
    def execute(self, sql, params=()):
        self._call('execute', (sql, params))

    def executemany(self, sql, params=()):
        self._call('executemany', (sql, params))

    def fetchone(self):
        return self._call('fetchone', proxy_class=RowProxy)

    def fetchmany(self, size):
        rows =  self._call('fetchmany', (size,), proxy_class=RowListProxy)
        if isinstance(rows, RowListProxy):
            rows = [r for r in rows]
        return rows

    def fetchall(self):
        rows =  self._call('fetchall', proxy_class=RowListProxy)
        if isinstance(rows, RowListProxy):
            rows = [r for r in rows]
        return rows

    def close(self):
        return self._call('close')

    # pyodbc specific
    def tables(self):
        return self._call('tables')

class RowProxy(Proxy):
    def __iter__(self):
        i = 0
        while True:
            try:
                col = self[i]
            except IndexError:
                break
            yield col
            i += 1

    def __getitem__(self, index):
        return self._call('__getitem__', (index,), proxy_class=BinaryProxy)

class BinaryProxy(Proxy):
    def getbinary(self):
        return self._call('getvalue')

class RowListProxy(Proxy):
    def __iter__(self):
        i = 0
        while True:
            try:
                row = self[i]
            except IndexError:
                break
            yield row
            i += 1

    def __getitem__(self, index):
        return self._call('__getitem__', (index,), proxy_class=RowProxy)

if __name__ == '__main__':
    import os
    #log = open('/dev/null', 'a')
    log = sys.stderr
    import traceback
    from logilab.common._pyodbcwrap import Binary # otherwise the isinstance test below will fail

    class RemoteControler(object):
        def __init__(self, read=sys.stdin, write=sys.stdout):
            self.objects = {}
            self.input = read
            self.output = write
            self.__objcount = 0

        def unregister(self, obj_id):
            try:
                del self.objects[obj_id]
                #print >> log, 'DELETED', obj_id
            except KeyError:
                pass

        def register(self, obj):
            self.__objcount += 1
            self.objects[self.__objcount] = obj
            obj.obj_id = self.__objcount
            return self.__objcount

        def control_loop(self):
            while True:
                try:
                    line = self.input.readline()
                except KeyboardInterrupt:
                    break
                if line == '':
                    break
                command, length = line.strip().split()
                #print >> log, command
                length = int(length)
                if length > 0:
                    try:
                        data = loads(self.input.read(length))
                        #print >> log, data
                    except KeyboardInterrupt:
                        break
                else:
                    data = None

                if command == 'CALL':
                    obj_id, method, args, kwargs = data
                    obj = self.objects[obj_id]
                    meth = getattr(obj, method)
                    try:
                        result = meth(*args, **kwargs)
                        #print >> log, 'result:', result
                        if result is None:
                            msg_head = 'NONE 0\r\n'
                            msg_data = ''
                        elif isinstance(result, RemoteWrapper):
                            msg_head = 'REF 0 %d\r\n' % result.obj_id
                            msg_data = ''
                        else:
                            msg_data = dumps(result)
                            msg_head = 'VAL %d\r\n' % len(msg_data)
                    except Exception, exc:
                        if not isinstance(exc, IndexError):
                            traceback.print_exc(file=sys.stderr)
                        msg_data = dumps((exc.__class__.__name__, exc.args))
                        msg_head = 'EXC %d\r\n' % len(msg_data)
                        #print >> log, 'EXC'
                elif command == 'NEW':
                    class_name, args, kwargs = data
                    klass = globals()[class_name]
                    try:
                        result = klass(*args, **kwargs)
                        msg_head = 'REF 0 %d\r\n' % result.obj_id
                        msg_data = ''
                    except Exception, exc:
                        traceback.print_exc(file=sys.stderr)
                        msg_data = dumps((exc.__class__.__name__, exc.args))
                        msg_head = 'EXC %d\r\n' % len(msg_data)

                elif command == 'DEL':
                    self.unregister(data)
                    msg_head = None
                    msg_data = None

                if msg_head is not None:
                    try:
                        self.output.write(msg_head)
                        self.output.flush()
                        if msg_data:
                            self.output.write(msg_data)
                            self.output.flush()
                    except IOError:
                        break
                #print >> log, 'STATS:', len(self.objects), 'objs alive'

    class RemoteWrapper(object):
        def __init__(self, wrapped):
            self.wrapped = wrapped
            REMOTE_CONTROLER.register(self)

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

        def __del__(self):
            if REMOTE_CONTROLER is not None:
                REMOTE_CONTROLER.unregister(self.obj_id)

        def __str__(self):
            return '<%s %d>' % (self.__class__.__name__, self.obj_id)

    class RemoteConnection(RemoteWrapper):
        def __init__(self, *args, **kwargs):
            cnx = dbapimodule.connect(*args, **kwargs)
            super(RemoteConnection, self).__init__(cnx)

        def cursor(self):
            return RemoteCursor(self.wrapped.cursor())



    class RemoteCursor(RemoteWrapper):
        def __init__(self, cursor):
            super(RemoteCursor, self).__init__(cursor)

        def _require_row_wrap(self):
            return True
            for col_desc in  self.wrapped.description:
                if col_desc[1] == dbapimodule.BINARY:
                    #print >> log, 'require wrap'
                    return True
            return False

        def execute(self, sql, params):
            #print >>log, sql, params
            if isinstance(params, (tuple, list)):
                tmp_params = []
                for p in params:
                    if isinstance(p, Binary):
                        p = dbapimodule.Binary(p.value)
                    tmp_params.append(p)
                params = tmp_params
            elif isinstance(params, dict):
                for k,v in params.iteritems():
                    #print >> log, k, v, Binary, isinstance(v, Binary)
                    if isinstance(v, Binary):
                        params[k] = dbapimodule.Binary(v.value)
            #print >>log, sql, params
            self.wrapped.execute(sql, params)

        def fetchone(self):
            row = self.wrapped.fetchone()
            if self._require_row_wrap():
                return RemoteRow(row)
            else:
                return row

        def fetchall(self):
            rows = self.wrapped.fetchall()
            #print >> log, 'fetchall', rows
            if self._require_row_wrap():
                return RemoteRowList(rows)
            else:
                return rows

        def fetchmany(self, size):
            rows = self.wrapped.fetchmany(size)
            if self._require_row_wrap():
                return RemoteRowList(rows)
            else:
                return rows

        def tables(self):
            self.wrapped.tables()


    class RemoteRow(RemoteWrapper):
        def __init__(self, row):
            super(RemoteRow, self).__init__(row)

        def __getitem__(self, index):
            #print >>log, 'getitem', self, self.wrapped, index
            data = self.wrapped[index]
            if isinstance(data, buffer):
                data = RemoteBinary(data)
            return data

    class RemoteRowList(RemoteWrapper):
        def __init__(self, rowlist):
            rows = [RemoteRow(r) for r in rowlist]
            super(RemoteRowList, self).__init__(rows)

        def __getitem__(self, index):
            #print >>log, 'getitem', self, self.wrapped, index
            return self.wrapped[index]

    class RemoteBinary(RemoteWrapper):
        def __init__(self, binary):
            super(RemoteBinary, self).__init__(binary)

        def getvalue(self):
            #print >>log, 'getvalue', self
            return self.wrapped[:]

    REMOTE_CONTROLER = RemoteControler()
    REMOTE_CONTROLER.control_loop()
