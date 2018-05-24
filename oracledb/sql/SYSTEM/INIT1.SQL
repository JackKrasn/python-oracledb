-- IB System Object Technical Support Scripts, Dec 1997
-- Create schema owner from installation wizard

spool init.lst

@@settings

-- please uncomment next 3 lines to use manually
-- ACCEPT u PROMPT 'Schema owner name (&&IBSO_OWNER) :' default &&IBSO_OWNER
-- ACCEPT dt PROMPT 'Default tablespace (&&INIT_TDEF) :'  default &&INIT_TDEF
-- ACCEPT tt PROMPT 'Temporary tablespace (&&INIT_TTMP) :' default &&INIT_TTMP

DEFINE u = &&IBSO_OWNER
DEFINE dt = &&INIT_TDEF
DEFINE tt = &&INIT_TTMP

@@UTILS\chk_sets
@@UTILS\chk_tsps '&&dt, &&tt'

-- please uncomment if you want drop existed user
-- prompt Dropping user &u ...
-- drop user &u cascade;
-- You can use kill.sql

SET VERIFY OFF
SET ECHO ON
create user &u identified by &u;
alter  user &u default tablespace &dt;
alter  user &u temporary tablespace &tt;
alter  user &u default role none;



spool off
exit
