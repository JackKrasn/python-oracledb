# Oracledb
**Oracledb** - пакет, написанный на Python для оркестрации БД Oracle. Поддерживаемые версии Oracle 12.1.0.2,
12.2.0.1 (CDB  и NON-CDB ).

С помощью пакета возможно:
  - создавать новую БД с пощощью утилиты dbca в silent режиме
  - создавать новую БД из бэкапа
  - удалять БД
  - выполнять sql/plsql запросы 
  - останавливать/запускать БД, в том числе и контейнерные
  - импортировать дамп

Структура пакета:
- **config.py** - задаются глобальные переменные.
- **db.py** - основной модуль. Описываются классы и методы.
- **dbexceptions.py** -  специфичные исключения, свяанные с БД.
- **dblogger.py** - настраивается логирование для пакета
- **orautils** - функции, которые могут использоваться вне данного пакета
- **sql/** - каталог, где хранятся sql/plsql скрипты.
- **templates/** - каталог, где хранятся все шаблоны jinja2.

## Getting Started
Пакет размещен в менеджере репозиториев [Nexus](https://bs-nexus.ftc.ru/)  

### Prerequisites
Должен быть установлены модули cx_Oracle(6.0.2), jinja2.

Поддерживая версия python 2.7. Запланирован переход на 3.6/3.7 

### Installing
Установить пакет
~~~
pip install oracledb
~~~

## Deployment
Импортировать пакет
~~~
import oracledb
~~~
Пример создания не контейнерной БД Oracle версии 12.1.0.2 из шаблона:
~~~python
import oracledb
import logging

oracledb.dblogger.root_logger.setLevel(logging.INFO)  # установить логирование в INFO. По умолчанию DEBUG 
db1=oracledb.db.LocalDb('o12102')
db1.create_from_tpl('pytest','/db1/oradata/pytest',cdb=False)
~~~

## Built With

* [cx_Oracle](https://cx-oracle.readthedocs.io/en/latest/) -  The module that enables access to Oracle Database and 
conforms to the Python database API specification.  Тесты проводились на версии модуля 6.0.2. В планах перейти на 7.0.0 
* [jinja2](http://jinja.pocoo.org/) - is a full featured template engine for Python.

## Versioning

Я использую [Семантическое Версионирование 2.0.0](https://semver.org/lang/ru/)

Достпуные релизы tags on this repository

## Authors

Evgeniy Krasnukhin (e.krasnukhin@cft.ru)


