set verify on
set feedback on
set serveroutput on

-- ACCEPT DEF_TEXT PROMPT 'Value for DEF_TEXT:' DEFAULT U
DEFINE DEF_TEXT = U
spool set_deft.log

begin

  update settings 
  set value=decode(substr('&&DEF_TEXT',1,1),'U','UNIX','W','WIN',nvl(value,'UNIX'))
  where name='DEF_TEXT';

  if sql%rowcount=0 then
     insert into settings(name,value,description) values(
       'DEF_TEXT', decode(substr('&&DEF_TEXT',1,1),'U','UNIX','W','WIN','UNIX'),
       '������������� ��������� ������ STDIO');

  end if;
  commit;
end;
/

select value from settings where name='DEF_TEXT';


spool off
quit
