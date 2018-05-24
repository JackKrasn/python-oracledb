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

define pipe_name = 'DEGUG'


SPOOL utils\cnv_owner.sql


declare
  old_user varchar2(30) := upper('&&old_user');
begin
  if upper(inst_info.owner) <> upper(user) then
    :ERROR_INFO := 'Current user is not IBSO owner';
  elsif user = nvl(old_user, user) then
    :ERROR_INFO:= 'Owner is not changed';
  end if;
  if :ERROR_INFO is not null then
    dbms_output.put_line('Prompt Error! ' || :ERROR_INFO);
    dbms_output.put_line('Exit');
    return;
  end if;	


  dbms_output.put_line('Prompt Updating ' || old_user || ' to ' || user || ' in tables...');
  dbms_output.put_line('set feedback on');
  dbms_output.put_line('set echo on');

  dbms_output.put_line('alter trigger users_before_ins_upd disable;');

  dbms_output.put_line('insert into USERS (name, username, type, properties)
    select replace(name,'''||old_user||''',''&&oxxx''), ''&&oxxx'', type, properties from USERS where username=''' || old_user|| ''';');

  dbms_output.put_line('insert into SUBJ_EQUAL (subj_id, equal_id, owner_id) values (''&&oxxx'', ''&&oxxx'', ''&&oxxx'');');

  dbms_output.put_line('update Z#USER set c_username=''&&oxxx'' where c_username=''' || old_user||'''
   and not exists(select 1 from z#user where c_username=''&&oxxx'');');

  dbms_output.put_line('alter trigger users_before_ins_upd enable;');

  dbms_output.put_line('Delete subj_equal where subj_id = ''' || old_user || ''';');
  	
  for c in
  (select uc.table_name, ucc.column_name
   from user_constraints uc, user_constraints uc2, user_cons_columns ucc
   where uc.constraint_type='R' and uc.r_constraint_name=uc2.constraint_name
         and uc2.table_name='USERS' and uc2.constraint_type='P' and ucc.constraint_name=uc.constraint_name
   order by uc.table_name,uc.constraint_name)
  loop
     dbms_output.put_line('update ' || c.table_name || ' set ' || c.column_name || '=''' || user || ''' ' ||
		          'where '  || c.column_name || '='''||old_user||''';');
  end loop;

  dbms_output.put_line('');
  dbms_output.put_line('var u number');
  dbms_output.put_line('exec secadmin.update_subj_equal;');
  dbms_output.put_line('exec :u := secadmin.fill_userid;');
  dbms_output.put_line('print u');
  dbms_output.put_line('');
  dbms_output.put_line('set echo off');
  dbms_output.put_line('set echo off');
  dbms_output.put_line('set feedback off');

end;
/

SPOOL OFF

SPOOL log.txt APPEND


@@cnv_owner;
commit;




