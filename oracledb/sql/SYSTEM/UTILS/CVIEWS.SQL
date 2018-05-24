set serverout on size 1000000
spool cviews.log
prompt rebuilding views
exec stdio.put_line_buf('Open: '||rtl.open)
exec after_install.recreate_vw_crit('1');
exec rtl.close
spool off
@@cgrant
