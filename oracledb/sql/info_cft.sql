-- Description: get info about cft platform settings.
-- Author: E.Krasnukhin(e.krasnukhin@cft.ru)
-- usage: from sqlplus
-- var FIO_HOME_DIR varchar2(100);
-- var CORE_VER varchar2(20);
-- var APP_VER varchar2(20);
-- @info_cft
-- from python:
-- binds_query(slurp('info_cft.sql'), {'FIO_HOME_DIR': 'STRING', 'CORE_VER': 'STRING', 'APP_VER': 'STRING'})
declare
    owner varchar2(20);
    sql_str varchar2(1000);
    no_such_table exception;
    pragma exception_init( no_such_table, -942 ); -- If two EXCEPTION_INIT pragmas assign different error codes to the same user-defined exception,
    --then the later pragma overrides the earlier pragma.
    --database_not_open exception;
    --pragma exception_init( no_such_table, -1219 );
begin
    execute immediate 'select value from audm.settings where name=''OWNERS''' into owner;
    sql_str := 'select value from '||owner||'.profiles where resource_name=''FIO_HOME_DIR''';
    execute immediate sql_str into :FIO_HOME_DIR;
    sql_str := 'select '||owner||'.inst_info.get_version from dual';
    execute immediate sql_str into :CORE_VER;
    sql_str := 'select '||owner||'.Z$SYSTEM_VERSION.GET_FULL_VERSION get_version from dual';
    execute immediate sql_str into :APP_VER;
exception
    when others then
        select 'NONE','NONE','NONE' into :FIO_HOME_DIR,:CORE_VER, :APP_VER from dual;
    --when others then
    --    select 'NONE','NONE','NONE' into :FIO_HOME_DIR,:CORE_VER, :APP_VER from dual;
end;