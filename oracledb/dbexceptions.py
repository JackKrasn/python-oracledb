# -*- coding: utf-8 -*-
import dblogger
import logging
import cx_Oracle

logger = logging.getLogger('oracledb.dbexceptions')
log_adapter = dblogger.DBLoggerAdapter(logger)


class Error(cx_Oracle.Error):
    def __init__(self, *args, **kwargs):
        log_adapter.error(args[0].message)
        print('SHIIIIIT')
        super(Error, self).__init__(*args, **kwargs)
        #log_adapter.error(args[0].message)


cx_Oracle.Error = Error


class DbException(Exception):
    pass


class DbEnvError(DbException):
    def __init__(self, msg, *args):
        log_adapter.error(msg, *args, extra={'methodName': 'DbEnvError()'})
        super(DbEnvError, self).__init__(msg, *args)


class DbArgMissError(DbException):
    def __init__(self, func_name, *args):
        # Подстановка имени функции и переданных аргументов в сообщение об ошибке
        msg = 'missing required arguments in {}(' + ', '.join(('{}',)*len(args)) + ')'
        msg = msg.format(func_name, *args)
        log_adapter.error(msg, extra={'methodName': func_name})
        super(DbArgMissError, self).__init__(msg)


class DbRmanExecError(DbException):
    def __init__(self):
        msg = 'rman executed with error'
        log_adapter.error(msg)
        super(DbRmanExecError, self).__init__(msg)
        exit(1)