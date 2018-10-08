# -*- coding: utf-8 -*-
import logging
import subprocess as sp
import dblogger
import jinja2
import dbexceptions
from StringIO import StringIO
import re
import config
import os


logger = logging.getLogger('oracledb.orautils')
log_adapter = dblogger.DBLoggerAdapter(logger)


def gen_from_tpl(tpl_dir, tpl, out_file=None, **kwargs):
    """
    Формирование файлов из шаблона.
    В шаблон tpl подставляются значения переменных, указанных в словаре kwargs
    и формируется конфигурационный файл или скрип, который записывается в файл указанный в качестве аргумента out_file.
    Если out_file не указан, то функция возвращает текст, сформированный из шаблона.
    :param tpl_dir: директория, где находятся файлы скриптов
    :param tpl: шаблон из которого нужно сформировать конфигурационный файл, скрипт и т.д.
    :param kwargs: это словарь параметров, которые будут подставлены в шаблон
    :param out_file: файл, который будет сформирован из шаблона
    :return: возвращает текст с подставленными переменными , если out_file=None
    """
    #log_adapter.debug('render: %s from template: %s', out_file, tpl)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(tpl_dir))
    template = env.get_template(tpl)
    if out_file is not None:
        with open(out_file, 'w') as f:
            f.write(template.render(**kwargs))
    else:
        return StringIO(template.render(**kwargs))
        #return template.render(**kwargs)


def oratab_exists(sid):
    """
    Проверяет есть запись в oratab для указанного sid
    :return: true если есть строка в ortab, иначе false
    """
    with open(config.ORATAB, 'r') as f:
        m = re.search(r"^{}:".format(sid), f.read(), re.M)
        if not m:
            return False
        return True


@dblogger.decorator_debug('set environement', log_adapter)
def oraenv(sid):
    """
    Определение окружениея для указанного сида.
    Окружение задается с помощью утилиты oraenv, поэтому данный сид должен быть указан
    в oratab
    :param sid: сид БД для которой необходимо определить environement. sid должен быть в oratab
    """
    needed_vars = ('ORACLE_HOME', 'ORACLE_BASE', 'LD_LIBRARY_PATH')
    if not oratab_exists(sid):
        raise dbexceptions.DbEnvError('sid {} does not exists in oratab'.format(sid))

    cmd = 'export ORAENV_ASK=NO; export ORACLE_SID={}; . oraenv >/dev/null 2>&1; env 2>/dev/null'.format(sid)
    proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE)
    pairs = map(lambda x: x.rstrip().split('=', 1), proc.stdout)
    pairs = filter(lambda x: x[0] in needed_vars, pairs)
    os.environ.update(dict(pairs))
    os.environ['ORACLE_SID'] = sid
    log_adapter.debug('environement: %s',dict(pairs))


@dblogger.decorator_debug('get oracle home version', log_adapter)
def get_oh_version(oracle_home):
    """
    Определяет версию ORACLE_HOME
    :param oracle_home: path ORACLE_HOME
    :return: oraver, compatible: Возвращает список из двух знычений, oracle_home в формате 12102.
    И  по сути таже версия Oracle, только с точками, формат 12.1.0.2. Нужно для параметра compatible
    """
    # Использовать strings более правильно, однако слишком долго выполняется.
    # Использую запрос к opatch. Важно, чтобы до этого не выполнялся oraenv, иначе вернет список патчей от хоума
    # заданного через oraenv
    #cmd = "strings {}/bin/oracle".format(oracle_home) +\
    #      " | perl -Wane 'if (/NLSRTL/) { print( (split/\./, $F[2], 5)[0..3]); exit 0; } }{ exit 1;'"
    cmd = "{}/OPatch/opatch lsinventory".format(oracle_home) +\
          " | perl -ne 'if (/^Oracle Database.*(\d{2}\.\d+\.\d+\.\d+)\.\d+/) { print $1; exit 0; } }{ exit 1;'"
    log_adapter.debug('%s', cmd)
    oraver = sp.check_output(cmd, shell=True)
    log_adapter.debug('oracle home version=%s', oraver)
    return oraver.replace(".", ""), oraver


def oratab_add(sid, oracle_home):
    """
    Добавление бд в oratab. Строка для добавления указана в oratab_line. Формат sid:oracle_home:N
    :param sid: sid бд, уоторую необходимо добавить
    :param oracle_home: oracle_home для заданной бд
    :return: true при успешном добавлении, иначе false
    """
    oratab_line = '\n' + sid + ':' + oracle_home + ':N'
    if not oratab_exists(sid):
        with open(config.ORATAB, 'a') as file:
            file.write(oratab_line)
            return True
    else:
        return False

# Для того, чтобы использовать бумажник нужно переопределить TNS_ADMIN.
# Для поддержки кроссплатформенности при каждом запуске формируется sqlnet.ora. И в зависимости от ОС формируется
# правильный путь.
#log_adapter.debug('create sqlnet.ora from template')
#gen_from_tpl(TPL_DIR, 'sqlnet.ora.j2', out_file=os.path.join(TNS_ADMIN, 'sqlnet.ora'), **{'WALLET_PATH': WALLET_PATH})
