rem *********************************************************
rem Перекомпиляция инвалидных объектов системы
rem (ALTER PACKAGE COMPILE BODY)
rem Запускается из-под SQL*Plus
rem *********************************************************
set feedback off
set heading off
set newpage 0
set pagesize 0
set echo off
set termout off
set verify off
set serveroutput on size 1000000
set linesize 250
set arraysize 1
set trimspool on
set trimout on
column xxx new_value oxxx noprint
select user xxx from dual;
spool &oxxx..sql
select 'prompt *** '||object_type||' '||object_name||chr(10)
||'ALTER '||DECODE(object_type,'PACKAGE BODY','PACKAGE',object_type)
||' '||object_name||DECODE(object_type,'PACKAGE BODY',' COMPILE BODY;',' COMPILE;')
||chr(10)||'sho err '||object_type||' '||object_name
  from user_objects
 where status='INVALID'
   and object_type in ('VIEW','PACKAGE','PACKAGE BODY','FUNCTION','PROCEDURE','TRIGGER');
spool off
set termout on
spool &oxxx..out
prompt Протокол компиляции пакетов
select 'Started  compiling packages - '||TO_CHAR(SYSDATE,'DD/MM/YY (HH24:MI:SS)') from dual;
@&oxxx.
select 'Finished compiling packages - '||TO_CHAR(SYSDATE,'DD/MM/YY (HH24:MI:SS)') from dual;
spool off
host del &oxxx..sql
set feedback on
set heading on
--EXIT
