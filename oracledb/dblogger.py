# -*- coding: utf-8 -*-
import logging.handlers
import os
from threading import Thread
from config import LOG_PATH


def decorator_debug(msg, log_adapter):
    def wrapper(fn):
        def wrapped(*args):
            message = msg
            if len(args) > 0:
                message = message + ' with arguments: ' + '%s '*len(args)
                log_adapter.debug(message, *args, extra={'methodName': fn.__name__})
            return fn(*args)
        return wrapped
    return wrapper


class DBLogger(logging.Logger):
    """
    Перегрузка makeRecord, чтобы добавить LogRecord атрибут 'methodName',
    значение которого по умолчанию равно значению атрибута 'funcName',
    но он является перезаписываемым с помощью extra, в отличие от остальных
    стандартных LogRecord атрибутов.
    """
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        rv = super(DBLogger, self).makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra)
        if extra is not None:
            if 'methodName' not in extra:
                rv.__dict__['methodName'] = rv.__dict__['funcName']

        return rv


class DBLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        if extra is None:
            extra = {}

        super(DBLoggerAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        """
        Перегрузка
        """
        try:
            self.extra['sid'] = os.environ['ORACLE_SID']
        except KeyError:
            self.extra['sid'] = 'UNKNOWN'

        try:
            self.extra['methodName'] = kwargs['extra']['methodName']
        except KeyError:
            pass

        try:
            self.extra['stdoutDisable'] = kwargs['extra']['stdoutDisable']
        except KeyError:
            self.extra['stdoutDisable'] = False

        msg, kwargs = super(DBLoggerAdapter, self).process(msg, kwargs)
        return msg, kwargs

    def subproc_logging(self, p_open, stdoutDisable=False):
        """
        Логирование subprocess.Popen
        Позволяет логировать средставми модуля logging stdout и stderr.
        Для одновременоого логирования stderr и stdout используются thread. Это необходимо для
        вывода логов ошибок в правильном порядке, т.е. сразу , а не после всего stdout
        :param p_open: subprocess.Popen object
        :return: subprocess return code
        """
        def handle_lines(pipe, fn):
            with pipe:
                for line in iter(pipe.readline, b''): # b'\n'-separated lines
                    fn(line)

        def stdout_handler(line):
            return self.info(line.rstrip(), extra={'methodName': 'subproc_logging', 'stdoutDisable': stdoutDisable})

        def stderr_handler(line):
            return self.error(line.rstrip(), extra={'methodName': 'subproc_logging'})

        Thread(target=handle_lines, args=[p_open.stdout, stdout_handler]).start()
        Thread(target=handle_lines, args=[p_open.stderr, stderr_handler]).start()


class ConsoleShutUp(logging.Filter):
    def filter(self, record):
        return not record.stdoutDisable


logging.setLoggerClass(DBLogger)
root_logger = logging.getLogger('oracledb')
root_logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
rotating_file = logging.handlers.RotatingFileHandler(LOG_PATH, backupCount=5)
fmt = "%(asctime)s [%(name)s/%(methodName)s]: %(levelname)s: sid=%(sid)s: %(message)s"
formatter = logging.Formatter(fmt, "%d.%m.%Y %H:%M:%S")
console.setFormatter(formatter)
rotating_file.setFormatter(formatter)
rotating_file.doRollover()
console.addFilter(ConsoleShutUp())
root_logger.addHandler(console)
root_logger.addHandler(rotating_file)

