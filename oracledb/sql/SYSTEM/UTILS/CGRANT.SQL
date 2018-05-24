rem *********************************************************
rem Производит раздачу грантов на интерфейсные пакеты
rem (GRANT EXECUTE ON <интерфейсный пакет> TO <схема>_USER)
rem Запускается из-под SQL*Plus
rem *********************************************************
set feedback off
set heading off
set newpage 0
set pagesize 0
set echo off
set termout off
set verify off
set serveroutput on size 500000
set linesize 250
set arraysize 1
set trimspool on
set trimout on
column xxx new_value oxxx noprint
select user xxx from dual;
spool &oxxx..sql
select 'GRANT EXECUTE ON '||object_name||' TO &oxxx._USER;'  
  from user_objects
 where object_type='PACKAGE' and object_name like 'Z$U$%';
spool off
set termout on
spool &oxxx..out
prompt Протокол раздачи прав на интерфейсные пакеты
select 'Started  - '||TO_CHAR(SYSDATE,'DD/MM/YY (HH24:MI:SS)') from dual;
@&oxxx.
select 'Finished - '||TO_CHAR(SYSDATE,'DD/MM/YY (HH24:MI:SS)') from dual;
spool off
rem host del &oxxx..sql
set feedback on
set heading on
EXIT
