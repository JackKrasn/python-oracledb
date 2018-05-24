set feedback off
set heading off
set newpage 0
set pagesize 0
set echo off
set verify off
set linesize 350
set arraysize 1
set trimspool on
set trimout on


/***********************************************************************************************
 готовим скрипт для назначения пользователям ролей для отчетов
***********************************************************************************************/

var v_All_users number;
exec :v_All_users := 1;

var v_AdminGrp number;
exec :v_AdminGrp := 1;

spool utils\c_syn_.sql


   select
  'prompt ***' || u.username||chr(10)||
  'exec secadmin.CreateSynonymsForSubject(''' || u.username || ''',false,true,false);'
  from
   (select username
      from users u
      where :v_All_users='1' and type='U' and exists (select 1 from all_users where username=u.username)
              and (lock_status is null or lock_status not in ('DELETED','TO_DELETE'))
              and (instr(nvl(properties,'|'),'|LOCK')=0 or instr(nvl(properties,'|'),'|REVISOR')>0)
    union
    select username
      from users u
      where :v_All_users='0' and type='U' and exists (select 1 from all_users where username=u.username)
      and (lock_status is null or lock_status not in ('DELETED','TO_DELETE'))
      and (instr(nvl(properties,'|'),'|INIT_SESSION')>0 or
         (instr(nvl(properties,'|'),'|REVISOR')>0 and not exists (select 1 from sec_domain_entries where user_id=u.username)) or
         (:v_AdminGrp='1' and exists (select 1 from Subj_Equal where Equal_Id='ADMIN_GRP' AND Subj_Id=u.username)))
    order by 1) u
    where username <> nvl(upper('&&old_user'), ' ');

 
spool off

spool log.txt append

/***********************************************************************************************
 Begin
***********************************************************************************************/

prompt Enable Resticted Session...


alter system enable restricted session;
exec rtl.lock_stop;
exec rtl.lock_stop;



/*********************************************************************************************** 
 Cоздаем роли
***********************************************************************************************/ 
prompt Creating Roles...
exec admin_mgr.create_roles;



/*********************************************************************************************** 
 Cоздаем контексты + выдаем системные гранты ролям _USER и проч. 
***********************************************************************************************/ 
exec after_install.grants(null);

/***********************************************************************************************
 Присваиваем соответствующие роли _USER/_ADMIN/др  всем активным пользователям системы
***********************************************************************************************/
prompt Grant roles to active users...
exec after_install.grant_roles(true);

prompt Disable Restricted Session...
alter system disable restricted session;
exec stdio.put_line_buf(rtl.open)

/***********************************************************************************************
 Перестраиваем системные представления
***********************************************************************************************/
prompt Rebuilding System Views...
exec sviews.create_all_sviews;
exec short_views.create_all;
exec after_install.create_diarys('1');


/***********************************************************************************************
 Генерируем роли для отчетов и наполняем их нужными грантами
***********************************************************************************************/
prompt Generating report roles...

alter package rtl compile body;
exec secadmin.generate_report_roles(140, false, true, true);


/***********************************************************************************************
 Выполняем скрипт @c_syn_.sql чтобы выдать нужным пользователям соответствующие роли для отчетов
***********************************************************************************************/
prompt Granting report roles to users...
@utils\c_syn_.sql;

prompt Rebuiling roles and views done.