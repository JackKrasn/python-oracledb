spool audm.log

@@settings

Prompt Creating auditor manager schema objects...
-- ACCEPT audit   PROMPT 'Schema Name for AUDIT manager (&&AUDM_OWNER):' default &&AUDM_OWNER
-- ACCEPT ibso    PROMPT 'IBSO owner schema (&&IBSO_OWNER) :'  default &&IBSO_OWNER

DEFINE audit = &&AUDM_OWNER
DEFINE ibso = &&IBSO_OWNER


@@UTILS\chk_sets

SET TERMOUT OFF
column xxx new_value audmgr noprint
select decode('&&audit','SYS','AUDM','','AUDM','&&audit') xxx from dual;
SET TERMOUT ON

exec &&audmgr..aud_mgr.stop;
exec dbms_lock.sleep(20);
audit session;
alter table &&ibso..users add
  (date_lock date, date_unlock date, lock_status varchar2(16));
exec &&audmgr..aud_mgr.get_settings(true);
exec &&audmgr..aud_mgr.del_owner('&&ibso');
exec &&audmgr..aud_mgr.add_owner('&&ibso');
exec &&audmgr..aud_mgr.submit;
spool off
exit
