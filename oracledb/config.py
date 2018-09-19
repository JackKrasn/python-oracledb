# -*- coding: utf-8 -*-
import os
import sys
import platform
import re

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SQL_DIR = os.path.join(BASE_DIR, 'sql')
TPL_DIR = os.path.join(BASE_DIR, 'templates')

if platform.system() == 'Windows':
#    os.environ['PATH'] = INSTANT_CLIENT + os.pathsep + os.environ['PATH']
    os.environ['NLS_LANG'] = 'RUSSIAN_CIS.CL8MSWIN1251'
    os.environ['NLS_LANG_CONSOLE'] = 'RUSSIAN_CIS.RU8PC866'
    os.environ['TMP'] = 'C:\TEMP'
else:
    os.environ['TMP'] = '/tmp'
    ORA_ADMIN = '/u/app/oracle/admin'

if os.path.exists('/usr/local/bin/dbhome'):
    with open('/usr/local/bin/dbhome') as dbhome:
        # Поиск значения ORATAB= в файле /usr/local/bin/dbhome
        match = re.search(r"^ORATAB=(\S+)", dbhome.read(), re.S | re.M)

    ORATAB = match.groups()[0]

LOG_DIR = os.environ['TMP']
LOG_FILE = os.path.split(sys.argv[0])[1] + '.log'
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
CONSOLE_SHUT_METHOD_POSTFIX = '#noconsole'
