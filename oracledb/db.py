#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import distutils.dir_util
import logging
import shutil
import subprocess as sp
import cx_Oracle
import dbexceptions
import dblogger
import orautils
import glob
import sys
import config
import os

logger = logging.getLogger('oracledb.db')
log_adapter = dblogger.DBLoggerAdapter(logger)
cx_Oracle.Error = dbexceptions.Error


def slurp(filename):
    with open(os.path.join(config.SQL_DIR, filename)) as f:
        return f.read()


def get_sql(filename):
    with open(os.path.join(config.SQL_DIR, filename)) as f:
        return tuple(s.strip() for s in f.read().rstrip().rstrip(';').split(';'))


def str_to_dict(str):
    # when str like 'compatible:12.1.0.2 local_listener:local_listener12102'
    list_from_str = [el for x in str.split() for el in x.split(':')]
    return {list_from_str[i]: list_from_str[i + 1] for i in range(0, len(list_from_str), 2)}


def cleanout(*args):
    """
    :param args: список файлов, которые необходимо удалить
    :return: ничего не возвращает
    """
    for f in args:
        try:
            os.remove(f)
        except OSError, e:
            log_adapter.warning('Eror %s - %s', e.filename, e.strerror)


# @dblogger.decorator_debug('create directories',log_adapter)
def dirs_create(*args):
    message = 'create directories ' + '%s ' * len(args)
    log_adapter.debug(message, *args)
    map(lambda x: distutils.dir_util.mkpath(x), args)


def files_exists(filepath):
    for filepath_object in glob.glob(filepath):
        if os.path.isfile(filepath_object):
            return True

    return False


class MyCursor(cx_Oracle.Cursor):

    def out_list(self):
        columns = [i[0] for i in self.description]
        return [dict(zip(columns, row)) for row in self]

    def out_dict(self):
        if len(self.description) != 2:
            raise Exception('query statement returns not 2 colums for out_dict()')

        return dict(self)

    def bind_cursor_query(self, statement):
        bind_cursor_var = self.var(cx_Oracle.CURSOR)
        self.execute(statement, cursor=bind_cursor_var)
        return bind_cursor_var.getvalue()

    def binds_query(self, statement, kwargs):
        """
        :param statement: sql выражение.
        Пример select decode(sys_context('USERENV','CON_ID'),1,'CDB','PDB') into :CON_TYPE from dual;
        :param kwargs: словарь переменных, которые описывают переменные в выражении
        kwargs = {'VAR_NAME': VAR_TYPE}
        VAR_TYPE тип переменной. Из документации к библиотеке  http://cx-oracle.readthedocs.io/en/latest/module.html
        :return: словарь {'название перменнойэ' : 'значение из БД'}
        """
        dict_bind_var = self.define_vars(kwargs)
        self.execute(statement, dict_bind_var)
        return {key: value.getvalue() for key,value in dict_bind_var.iteritems()}

    def plsql_query_output(self, statement):
        self.callproc('dbms_output.enable')
        self.execute(statement)
        statusVar = self.var(cx_Oracle.NUMBER)
        lineVar = self.var(cx_Oracle.STRING)
        output_list = None
        while True:
            self.callproc('dbms_output.get_line', (lineVar, statusVar))
            if statusVar.getvalue() != 0:
                break
            output_list = lineVar.getvalue()
            #.split()

            if len(output_list) % 2 != 0:
                raise(Exception('plsql output list length is odd'))

        return output_list

    def ddl_execute(self, statement, oerr=None):
        log_adapter.debug('%s',statement)
        try:
            self.execute(statement)
        except cx_Oracle.DatabaseError, e:
            error, = e.args
            if error.code == oerr:
                log_adapter.debug(e.message)
            else:
                log_adapter.error(e.message)
                sys.exit(1)

    def define_vars(self, kwargs):
        return {key: self.var(getattr(cx_Oracle, value.upper())) for key, value in kwargs.iteritems()}


class MyConnection(cx_Oracle.Connection):
    def cursor(self):
        return MyCursor(self)


class Listener(object):

    def __init__(self, listname, oracle_version):
        self.listname = listname
        sid = 'o' + str(oracle_version)
        orautils.oraenv(sid)
        self.oracle_home = os.environ['ORACLE_HOME']
        self.lsnr_ctl = os.path.join(self.oracle_home, 'bin', 'lsnrctl')

    def lsnrctl(self, command):
        cmd = '{} {} {}'.format(self.lsnr_ctl, command, self.listname)
        sp.check_output(cmd, shell=True)

    def get_port_number(self):
        cmd = '{} {}'.format(self.lsnr_ctl, 'status ' + self.listname)
        try:
            out = sp.check_output(cmd, shell=True)
        except sp.CalledProcessError:
            log_adapter.error('can not get status of the listener %s', self.listname)
            return 0

        p = re.compile('PORT\s*=\s*(\d+)', re.S | re.M)
        m = re.search(p, out)
        return m.group(1)


class Db(object):
    def __init__(self, tns, wallet=False, user='sys', passw='sys'):
        self.tns = tns
        self.param = {}
        self.info_db = {}
        self.info_con = {}
        self.info_instance = {}
        self.info_cft = {}
        self.info_comp = {}
        #self.sys_pass = "sys"
        self.conn = None
        if wallet:
            self.conn_string = '/@{}'.format(self.tns)
        else:
            self.conn_string = '{}/{}@{}'.format(user, passw, self.tns)
        self.oracle_home = os.environ['ORACLE_HOME']
        self.oracle_base = os.environ['ORACLE_BASE']
        self.rman = os.path.join(self.oracle_home, 'bin', 'rman')
        #self.connection_init()

    def cur(self):
        return self.conn.cursor() if self.conn is not None else None

    def get_info_instance(self):
        cur = self.cur()
        self.param = cur.bind_cursor_query(slurp('parameters.sql')).out_dict()
        self.info_instance = cur.bind_cursor_query(slurp('info_instance.sql')).out_list()[0]
        if self.param['db_recovery_file_dest'] is None:
            fra = None
        else:
            fra = os.path.join(self.param['db_recovery_file_dest'], self.info_instance['INSTANCE_NAME'].upper())

        self.param.update({'fra': fra})

    def get_info_db(self):
        cur = self.cur()
        if self.info_instance['STATUS'] != 'STARTED': #get information from v$database. Database must be in mount mode
            self.info_db = cur.bind_cursor_query(slurp('info_db.sql')).out_list()[0]
            # Получить список компонент, которые установлены. ВНачале получаем список словарей.Структура вида
            # [{},{}], а затем преобразую в словарь {COMP_ID:STATUS}
            self.info_comp = {id['COMP_ID']: id['STATUS'] for id in cur.bind_cursor_query(slurp('info_comp.sql')).out_list()}
            self.info_con = cur.binds_query(slurp('info_con.sql'), {'CON_NAME': 'STRING', 'CON_ID': 'NUMBER',
                                                                    'CON_TYPE': 'STRING'})
            self.info_db.update(self.info_con)

    def connection(self):
        if self.conn  is None:
            try:
                self.conn = MyConnection(self.conn_string, mode=cx_Oracle.SYSDBA)
            except cx_Oracle.DatabaseError, e:
                error, = e.args
                log_adapter.error(error.message)
                sys.exit(1)

        self.get_info_instance()
        self.get_info_db()
        self.get_info_cft()
        return self.conn

    def connection_init(self):
        try:
            self.conn = MyConnection(self.conn_string, mode=cx_Oracle.SYSDBA)
            self.get_info_instance()
            self.get_info_db()
            self.get_info_cft()
        except cx_Oracle.DatabaseError, e:
            error, = e.args
            if error.code == 1034:
                log_adapter.warning('ORA-01034: ORACLE not available')

    def _run_cmd(self, cmd, stdoutDisable=False):
        log_adapter.info('executing: %s', cmd)
        p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        log_adapter.subproc_logging(p, stdoutDisable=stdoutDisable)
        return p.wait()

    def run_rman(self, script, conn='target', stdoutDisable=False):
        """
        Подготовливает команду для запуска через метод _run_cmd.
        На основе входных данных формируется команда для утилиты rman.
        :param script: рмановский скрипт или команда. Если начинается с @ - рмановский скрипт, c <<< команда.
        Пример: <<<"list backup;"  @script.sql
        :param conn: может принимать 2 значения auxiliary или target. По умолчанию target
        :return:
        """
        connect_string = ' {} '.format(conn) + self.conn_string
        cmd = self.rman + connect_string + ' {}'.format(script)
        return self._run_cmd(cmd, stdoutDisable=stdoutDisable)

    def get_info_cft(self):
        """
        Информация о платформе ЦФТ-Банк развитие. Расположение FIO, версии ТЯ и ПЯ
        :return:
        """
        cur = self.cur()
        if self.info_instance['STATUS'] != 'STARTED':
            self.info_cft = cur.binds_query(slurp('info_cft.sql'),
                                            {'FIO_HOME_DIR': 'STRING', 'CORE_VER': 'STRING', 'APP_VER': 'STRING'})

    def pdb_close(self, con_name=''):
        """
        Остановить контейнерную БД
        :param con_name: Имя контейнера, который необходимо остановить. По умолчанию команда выполнится на текущем
        контейнере.
        """
        cur = self.cur()
        #ORA-65020: pluggable database already close. Ignore this error
        cur.ddl_execute('alter pluggable database {} close immediate'.format(con_name), oerr=65020)

    def set_con(self, con_name='CDB$ROOT'):
        """
        Перейти в указанный контейнер
        :param con_name: имя контейнера в который необходимо перейти
        """
        cur = self.cur()
        cur.ddl_execute('alter session set container={}'.format(con_name))
        self.get_info_db()

    def pdb_open(self, con_name='', mode='READ WRITE'):
        """
        Открыть контейнерную БД. По умолчанию открывается текущая БД в режиме READ WRITE
        :param con_name: имя контейнера
        :param mode: допустимые значения READ WRITE, READ ONLY. В каком режиме открыть БД.
        """
        cur = self.cur()
        cur.ddl_execute('alter pluggable database {} open {}'.format(con_name, mode))

    def pdb_drop(self, con_name):
        cur = self.cur()
        cur.ddl_execute('drop pluggable database {} including datafiles'.format(con_name))

    def copy_pdb(self, src_con_name, dst_con_name, snap=False):
        """
        :param src_con_name:  название контейнера с которого необходимо сделать копию
        :param dst_con_name:  контейнер, который создается, т.е. новый
        :param snap: создается снапшот или нет
        """
        if snap:
            snap = 'snapshot copy'
        else:
            snap = ''

        cur = self.cur()
        cur.ddl_execute('create pluggable database {} from {} {}'.format(dst_con_name, src_con_name, snap))


def just_warning_exception(ora_err):
    def wrapped_with_warning(fn):
        def wrapped_with_warning_inner(self):
            try:
                fn(self)
            except cx_Oracle.DatabaseError, e:
                error, = e.args
                if error.code == ora_err:
                    log_adapter.warning(e.message)
                else:
                    log_adapter.error(e.message)
                    sys.exit(1)

        return wrapped_with_warning_inner
    return wrapped_with_warning


def decorator_startup(func):
    """
    Декоратор. Обвертка для методов mount и open
    :param func: имя функции которая будет вызвана позже в функции wrapped. Таким образом передаются аргументы.
    Декоратор был применен для уменьшения кода.
    Используется для запуска БД. Если соединение не установленнно(conn=None), значит, необходимо сначала запустить БД в
    режиме nomount, а затем выполнить декорируемый метод(open или mount) и собрать инфомацию об истансе и бд.
    """
    def wrapper(method_to_decorate):
        def wrapped(self):
            if self.conn is None: # conn заполняется в конструкторе класса. Если оно None, значит, инстансов остановлен
                func(self)
            method_to_decorate(self) # декорируемый метод
            self.get_info_instance()  # собрать информацию об инстансе
            self.get_info_db() # собрать информацию о БД
        return wrapped
    return wrapper


def decorator_datapatch(*args, **kwargs):
    """
    Декоратор для запуска datapatch после создания БД.  Это обвертка над методом _create и create_from_tpl.
    method_to_decorate - метод, над которым пишется обвертка.
    *args - опциональные аргументы
    **kwargs - позиционные аргументы
    Пример:
    При создании БД из шаблона, используется метод create_from_tpl. В методе нужно указать несколько аргументов, поскольку их количество неизвестно,
    то передаю так *args, **kwargs.
    :type kwargs: позиционные параметры оборачиваемого метода
    """
    def wrapper(method_to_decorate):
        def wrapped(self, *args, **kwargs):
            method_to_decorate(self, *args, **kwargs)
            cmd = os.path.join(self.oracle_home, 'OPatch', 'datapatch') + ' -verbose'
            self._run_cmd(cmd)
        return wrapped
    return wrapper
# class PlatformCft(Db):
#     def __init__(self):


class LocalDb(Db):
    def __init__(self, sid):
        orautils.oraenv(sid)
        super(LocalDb,self).__init__(tns=None)
        self.conn_string = '/'
        self.sid = sid
        self.oraver, self.compatible = [str(x) for x in orautils.get_oh_version(self.oracle_home)]
        # self.oraver='12102'
        self.oh_templates = os.path.join(self.oracle_home, 'assistants', 'dbca', 'templates')
        self.init_param = {
            'local_listener': 'ORALIST' + self.oraver,
            'sid': sid,
            'compatible': self.compatible
        }
        self.connection_init()

    def nomount(self):
        if self.conn is None:
            log_adapter.info('startup nomount')
            conn_prelim = cx_Oracle.connect("/", mode=cx_Oracle.SYSDBA | cx_Oracle.PRELIM_AUTH)
            conn_prelim.startup()
            self.connection()

    @decorator_startup(nomount)
    def mount(self):
        if self.info_instance['STATUS'] not in ('MOUNTED','OPEN'):
            log_adapter.info('startup mount')
            self.cur().ddl_execute("alter database mount")

    # декоратор. Функция open оборачивается в декоратор decorator_startup
    @decorator_startup(nomount)
    def open(self):
        """
        Открытие БД. Если инстанс не запущен, то вызывается вначале метод mount, который в свою очередь
        вызовет метод mount
        :return:
        """
        if self.info_instance['STATUS'] != 'OPEN':
            self.mount()
            log_adapter.info('startup open')
            self.cur().ddl_execute("alter database open")

    def _shut(self, mode):
        """
        Внутренний метод, вызывается в shut_immediate и shut_abort.
        Останавливает БД в зависимости от заданного режима mode.
        Очищает структуры данных, связанных  с БД
        :param mode: режим остановки БД
        подробнее https://cx-oracle.readthedocs.io/en/latest/connection.html#Connection.shutdown
        """
        self.conn.shutdown(mode=mode)
        self.info_instance = {}
        self.info_db = {}
        self.param = {}
        self.cur().close()
        self.conn.close()
        self.conn = None

    def shut_immediate(self):
        """
        Коректная остановка БД. Выполнение команды shutdown immediate.
        """
        if self.conn is not None:
            log_adapter.info('shutdown immediate')
            self.conn.shutdown(cx_Oracle.DBSHUTDOWN_IMMEDIATE)
            self.cur().ddl_execute("alter database close normal")
            self.cur().ddl_execute("alter database dismount")
            self._shut(cx_Oracle.DBSHUTDOWN_FINAL)

    def shut_abort(self):
        """
        Выключение БД. Выполнение команды shutdow abort.
        Вызывается метод _shut в котором и останавливается БД и обнулюются структуры,
        в которых хранится информация о БД
        """
        if self.conn is not None:
            log_adapter.info('shutdown abort')
            self._shut(cx_Oracle.DBSHUTDOWN_ABORT)

    def pfile_create(self):
        """
        Создание файла параметров pfile из шаблона init.ora.j2
        :return: путь к pfile
        """
        pfile = os.path.join(self.oracle_home, 'dbs', 'init{}.ora'.format(self.sid))
        orautils.gen_from_tpl(config.TPL_DIR, 'init.ora.j2', out_file=pfile, **self.init_param)
        return pfile

    def orapw_create(self):
        """
        Создание файла паролей(orapw).
        """
        orapwfile = os.path.join(self.oracle_home, 'dbs', 'orapw{}'.format(self.sid))
        log_adapter.debug('create orapw file %s', orapwfile)
        cmd='$ORACLE_HOME/bin/orapwd file={} password=sys force=yes'.format(orapwfile)
        log_adapter.debug('%s', cmd)
        sp.check_output(cmd, shell=True).rstrip()

    def rman_dup_bkp(self, bkp_loc, parallel, until_time):
        """
        Cоздание БД из бэкапа с помощью rman duplicate. БД должна быть в nomount mode.
        БД создается командой: duplicate database to SID backup location='backup_path';
        RMAN скрипт формируетя из шаблона duplicate_from_bkp.rman.j2 и сохраняется в /tmp/duplicate_from_bkp.rman
        :param bkp_loc: расположение бэкапа
        :param parallel: количество каналов, которые будут открыты, т.е. параллельность
        :param until_time: на какое время восстановить БД. Формат времени dd.mm.yyyy hh24:mi:ss
        Значение параметра подставляется в команду rman set until time=(to_date(:param),'dd.mm.yyyy hh24:mi:ss').
        """
        log_adapter.info('rman duplicate from backup %s', bkp_loc)
        rman_tpl='duplicate_from_bkp.rman.j2' #шаблон для скрипта
        rman_script=os.path.join('/tmp',rman_tpl.replace('.j2','')) #имя скрипта
        # param - словарь параметров для формирования  скрипта из шаблона
        param = {
            'until_time': until_time,
            'sid': os.environ['ORACLE_SID'],
            'parallel': parallel,
            'bkploc': bkp_loc
        }
        # формирование скрипта из шаблона
        orautils.gen_from_tpl(config.TPL_DIR, rman_tpl, out_file=rman_script, **param)
        self.run_rman('@' + rman_script, 'auxiliary')

    def prepare_env(self):
        """
        Подготовливает окружение к созданию БД.
        Выполнгяет следующие действия:
        - создает файл паролей
        - создает файл параметров pfile
        - создает директории adump и oradata
        - создает spfile из pfile
        - регистрирует бд в oratab
         """
        self.orapw_create()
        pfile = self.pfile_create()
        # необходимо создать каталоги adump и  oradata
        adump_dir = os.path.join(config.ORA_ADMIN, self.sid, 'adump')
        dirs_create(self.init_param['oradata'], adump_dir)
        self.nomount()
        # Создание spfile из pfile. Если spfile уже существует, то исключение обработает ошибку ORA-32002
        # выдаст warning и продолжит работу
        self.cur().ddl_execute("create spfile from pfile='{}'".format(pfile),
                               32002)  # ORA-32002: cannot create SPFILE already being used by the instance
        log_adapter.debug('remove pfile %s', pfile)
        # Добавление бд в oratab
        orautils.oratab_add(self.sid,self.oracle_home)
        os.remove(pfile) if os.path.exists(pfile) else None  # удаление pfile, т.к. был создан spfile


    @decorator_datapatch()
    def create_from_tpl(self, newsid, oradata, nls='CL8ISO8859P5', archive_mode=False, cdb=False):
        """
        Создание БД из шаблона с помощью DBCA
        :param newsid: sid для создаваемой БД
        :param oradata: значение параметра db_create_file_dest. Т.е. расположение файлов БД
        :param nls: кодировка базы данных
        :param archive_mode: включить архивный режим или нет
        :param cdb: создаваемая БД контейнерная иди нет. По умолчанию false => БД неконтейнерная.
        """
        self.sid = newsid
        os.environ['ORACLE_SID'] = newsid
        dbca_rsp = 'dbca_' + self.oraver + '.rsp.j2'  # шаблон response file для DBCA. Формат dbca.12102.rsp.j2
        #dbca_tpl= 'General_Purpose.{}.dbc.j2'.format(self.oraver)  # j2 шаблон для шаблона dbca в dbc
        if cdb:
            dfb_file = 'db_{}_cdb_{}.dfb'.format(self.oraver, nls)
        else:
            dfb_file = 'db_{}_noncdb_{}.dfb'.format(self.oraver, nls)

        if files_exists(os.path.join(self.oh_templates, dfb_file) + '*'):  # Если шаблон существует по стандартному пути
            dbca_tpl = dfb_file.replace('_{}.dfb'.format(nls), '.dbc.j2')
            dfb_exists = True
        else:
            dbca_tpl = 'db_{}.dbt.j2'.format(self.oraver)
            dfb_exists = False

        # dbca_tpl = 'dbca.{}.dbt.j2'.format(self.oraver)
        rsp_file = os.path.join('/tmp', dbca_rsp.replace('.j2', ''))  # response файл полученный из шаблона
        tpl_file = os.path.join('/tmp', dbca_tpl.replace('.j2', ''))
        self.init_param.update({'oradata': oradata,
                                'sid': self.sid,
                                'nls_characterset': nls,
                                'oracle_base': self.oracle_base,
                                'oracle_home': self.oracle_home,
                                'template':  tpl_file,  # dbca_tpl.replace('.j2', ''),
                                'shared_pool_size': '1G',
                                'archive_mode': archive_mode,
                                'cdb': cdb})
        log_adapter.debug(self.init_param)
        dbca_cmd = os.path.join(self.oracle_home, 'bin', 'dbca') + ' -createDatabase -silent -responseFile ' + rsp_file
        # создание response файла из шаблона
        orautils.gen_from_tpl(config.TPL_DIR, dbca_rsp, out_file=rsp_file, **self.init_param)
        orautils.gen_from_tpl(config.TPL_DIR, dbca_tpl, out_file=tpl_file, **self.init_param)
        # Копирование шаблона из каталога со всеми шаблонами в каталог шаблонов dbca, чтобы его смог подтянуть dbca
        # shutil.copy2(tpl_file, self.oh_templates)
        dirs_create(oradata)
        log_adapter.info('CDB:%s   NLS:%s    Archive_mode:%s    Oradata:%s', cdb, nls, archive_mode, oradata)
        if dfb_exists:
            log_adapter.info('Type of DBCA Templates:SEED   path:%s', tpl_file)
        else:
            log_adapter.info('Type of DBCA Templates:NONSEED   path:%s', tpl_file)
        self._run_cmd(dbca_cmd)
        self.connection()
        # Не устанавливаются некоторые параметры, указанные в шаблоне для dbca.
        # например, local_listener или shared_pool_size. Пробовал указывать в initTrans в rsp файле и
        # в dbt файле. Часть параметров подтягивается, а часть нет. Поэтому решил указать в явном виде.
        for par in ['local_listener', 'shared_pool_size']:
            self.cur().ddl_execute('alter system set {}={}'.format(par, self.init_param[par]))
        # Не удается за раз выполнить запрос по созданию ТБП. Выскакивает ошибка переполнения буфера
        # Поскольку get_sql возвращает кортеж комманд разделенных по ";"
        # Обхожу кортеж в цикле и выполняю каждую команду по отдельности
        # for sql in get_sql('create_tablespaces.sql'):
        #    self.cur().ddl_execute(sql)
        # hotfix 0.1.3
        # в 12.2.0.1 не создаются файлы в шаблоне dbt. Ковырялся не смог понять почему, поэтому добавляю
        # файлы уже после создания БД.
        if not dfb_exists:
            for sql in get_sql('add_datafiles.sql'):
                self.cur().ddl_execute(sql)
        cleanout(rsp_file, tpl_file)

    @decorator_datapatch()
    def _create(self, newsid, oradata, fn_run, fn_run_args=(), fn_pre=None, fn_pre_args=()):
        self.sid = newsid
        self.init_param.update({'oradata': oradata, 'sid': self.sid})
        os.environ['ORACLE_SID'] = self.sid
        if fn_pre is not None:
            fn_pre(*fn_pre_args)
        return fn_run(*fn_run_args)

    def create_from_bkp(self, newsid, oradata, bkp_loc, parallel=8, until_time=None):
        return self._create(newsid, oradata,
                            fn_run=self.rman_dup_bkp,
                            fn_run_args=(bkp_loc, parallel, until_time),
                            fn_pre=self.prepare_env)

    def update_from_bkp(self, bkp_lock, parallel=8, until_time=None):
        # Необходимо сохранить spfile, т.к. drop database удаляет spfile.
        # словарь param будет обнулен в результат функции shut_abort() бд
        # поэтому сохраняем его перед удалением БД
        param = self.param
        bkpspfile = self.drop(flag_bkp_spfile=True)
        # если bkpspfile=None, значит, используется pfile, а он не удаляется при использовании функции drop
        if bkpspfile is not None:
            shutil.move(bkpspfile, param['spfile'])
        return self._create(self.sid, param['db_create_file_dest'],
                            fn_run=self.rman_dup_bkp,
                            fn_run_args=(bkp_lock, parallel, until_time),
                            fn_pre=self.nomount)

    def drop(self, flag_bkp_spfile=False):
        """
        Удаление БД с помощью sqlplus. При сохранении spfile возвращает расположение бэкапа spfile.
        Если БД использует pfile, то он не удаляется.
        Выполняется последовательность:
        SQL> startup force mount;
        SQL> alter system enable restricted session;
        SQL> drop database;
        : bkp_spfile: boolean. Сделать бэкап spfile или нет
        :return:
        """
        log_adapter.info('drop database using sqlplus')
        bkpspfile = None
        if flag_bkp_spfile and self.param['spfile'] is not None:
            log_adapter.debug('backup spfile')
            bkpspfile = self.param['spfile'] + '.bkp'
            shutil.copy2(self.param['spfile'], bkpspfile)

        self.shut_abort()
        self.mount()
        self.cur().ddl_execute('alter system enable restricted session')
        self.cur().ddl_execute('drop database')
        self.shut_abort()
        return bkpspfile

    def delete(self, with_backups=False):
        """
        Удаление БД, используя утилиту dbca.
        Утилита dbca удаляет датафайлы, файл паролей, файл параметров, каталоги, регистрацию в oratab и листенере.
        """
        #Удалять бэкапы или нет. Если условие истинно, то удалить бэкапы и каталог с fra.
        if with_backups:
            self.run_rman('<<<"delete noprompt backup;"')

        # reset sys password
        self.cur().ddl_execute('alter user sys identified by sys')

        #delete database
        cmd = '{}/bin/dbca -silent -deleteDatabase -sourceDB {} ' \
              '-sysDBAUserName sys -sysDBAPassword sys '.format(self.oracle_home, self.sid)

        # log_adapter.info(cmd)
        # p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        # log_adapter.subproc_logging(p)
        # p.wait()
        self._run_cmd(cmd)

        # Если необходимо удалить бэкапы, то после удаления бэкапов необходимо удалить fra
        # Если fra был задан, то грохнуть его. Если каталоги были расположены в каком-то другом каталоге,
        # то такой каталог останется
        if with_backups:
            if self.param['fra'] is not None:
                log_adapter.info('delete fra %s',self.param['fra'])
                if os.path.exists(self.param['fra']):
                    shutil.rmtree(self.param['fra'])
                else:
                    log_adapter.error('no such directory %s', self.param['fra'])


    def backup_keep(self, bkploc='/dbbackup', tag='KEEP_BACKUP', keep_day=14, parallel=8):
        """
        Создание бэкапа с опцией keep.
        :param bkp_loc: абсолюдный путь, где будет хранитсья бэкап. Путь по умолчанию /dbbackup/sid
        :param tag: tag бэкапа, по умолчанию KEEP_BACKUP
        :param keep_day: количество дней. После заданного количества дней бэкап будет считаться утстаревшим
        и на него будут действовать правила по удалению устаревших бэкапов
        :return:
        """
        rman_tpl = 'backup_keep.rman.j2'  # шаблон для скрипта
        rman_script = os.path.join('/tmp', rman_tpl.replace('.j2', ''))  # имя скрипта
        #bkploc = os.path.join(bkploc, self.sid)
        # param - словарь параметров для формирования  скрипта из шаблона
        param = {
            'tag': tag,
            'keep_day': keep_day,
            'parallel': parallel,
            'bkploc': bkploc
        }
        log_adapter.info('create rman backup with keep option ')
        if self.info_db['LOG_MODE'] != 'ARCHIVELOG':
            log_adapter.info('database not in archivelog mode')
            self.shut_immediate()
            self.mount()

        dirs_create(bkploc)
        # формирование скрипта из шаблона
        orautils.gen_from_tpl(config.TPL_DIR, rman_tpl, out_file=rman_script, **param)
        rc = self.run_rman('@' + rman_script)

        # if self.info_instance['STATUS'] != 'OPEN':
        #     self.open()

    def impdp(self, dumpfile, *args):
        """
        Импорт с помощью утилиты датапамп impdp
        :param args: параметры для импорта
        :return:
        """
        dir = os.path.split(dumpfile)[0]
        filename = os.path.split(dumpfile)[1]
        os.chdir(dir)  # переходим в директорию с дампом
        self.cur().ddl_execute('create or replace directory DATA_PUMP as \'' + dir + '\'')
        cmd = r'impdp \'/as sysdba\' DIRECTORY=DATA_PUMP DUMPFILE=' + filename
        #      ' LOG_FILE=import.log
        for i in args:
            cmd += ' ' + i
        cmd += ' 2>&1' # impdp log импорта валится в stderror. Если так не делать, то сообщения с категорией ERROR
        self._run_cmd(cmd, stdoutDisable=True)#запускаем сам импорт


