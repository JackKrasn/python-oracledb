SET SERVEROUT ON SIZE UNLIMITED
SET VERIFY OFF

column xxx new_value oxxx noprint
select user xxx from dual;

SPOOL log.txt

DEFINE is_user_changed = N
SPOOL OFF

def old_user = ''

SET TERMOUT OFF
SET FEEDBACK OFF
SPOOL utils\step1.sql
BEGIN 
 dbms_output.put_line('SET TERMOUT ON');
 dbms_output.put_line('SPOOL log.txt APPEND');   
 if upper('&&is_user_changed') not in ('Y', 'N') then
   dbms_output.put_line('Prompt Error: choice must be Y or N. Exit.');
   dbms_output.put_line('Exit');
 elsif upper('&&is_user_changed') = 'Y' then
   dbms_output.put_line('ACCEPT old_user PROMPT "Old IBSO User[IBS]:" dEFAULT IBS');
 end if;
END;
/

SPOOL OFF
@utils\step1.sql

DEFINE is_ora_changed = N
PROMPT

SPOOL OFF
SET TERMOUT OFF
SET FEEDBACK OFF

variable error_info char(1000)


SPOOL utils\step2.sql REPLACE
BEGIN
 dbms_output.put_line('SET TERMOUT ON');
 dbms_output.put_line('SPOOL log.txt APPEND');   

 if upper('&&is_ora_changed') not in ('Y', 'N') then
   dbms_output.put_line('Prompt Error: choice must be Y or N. Exit.');
   dbms_output.put_line('Exit');
 end if;

 -- ���� ������� ��� ���������:
 if upper('&&is_user_changed') = 'Y' then
  dbms_output.put_line('Prompt Changing IBSO Owner...');
  dbms_output.put_line('Prompt Old Owner = ' || upper('&&old_user'));
  dbms_output.put_line('Prompt New Owner = &&oxxx');
  dbms_output.put_line('@@chk_owner.sql');
 end if;
 
 if upper('&&is_ora_changed') = 'Y' then
  dbms_output.put_line('Prompt Fulfill the full upgrade to the necessary version.');
  dbms_output.put_line('Exit');	
 end if;

END;
/

SPOOL OFF
@utils\step2.sql

SPOOL log.txt APPEND

prompt Rebuiling roles and views...
@utils\rebuild.sql
exit
