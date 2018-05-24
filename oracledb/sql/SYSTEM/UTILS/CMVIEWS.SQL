set serverout on size 1000000
spool cmviews.log

@@./settings

-- please uncomment next line to use manually
-- ACCEPT u PROMPT 'Schema owner name (&&IBSO_OWNER) :' default &&IBSO_OWNER
DEFINE u = &&IBSO_OWNER
prompt rebuilding materialized views

begin
  for c in(select u.MVIEW_NAME as mvname, u.owner as owner from all_mviews u where u.owner = '&u')
    loop
      begin
        dbms_mview.refresh( list => c.owner || '.' || c.mvname, method => 'C' );
        dbms_output.put_line(c.mvname || ' - ok');
      exception when others then
        dbms_output.put_line('complete refresh '|| c.mvname || ' failed due to');
        dbms_output.put_line(dbms_utility.format_call_stack);
        dbms_output.put_line(dbms_utility.format_error_backtrace);
      end;
    end loop;
end;
/

spool off

quit