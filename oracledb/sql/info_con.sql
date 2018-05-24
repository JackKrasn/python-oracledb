-- Description: get info about container. Result: CON_NAME = NONCDB, CDB, PDB_SNAPSHOT, PDB.
-- Author: E.Krasnukhin(e.krasnukhin@cft.ru)
-- usage: from sqlplus
-- var CON_NAME varchar2(20);
-- var CON_ID number;
-- var CON_TYPE varchar2(20);
-- @info_con
-- from python:
-- binds_query(slurp('info_con.sql'), {'CON_NAME': 'STRING', 'CON_ID': 'NUMBER', 'CON_TYPE': 'STRING'})
declare
 ver varchar2(20);
 parent_id number;
 con_name varchar2(20);
 con_id number;
begin
  select substr(version,1,2) into ver from v$instance;
  if ver = '12' THEN
      select SYS_CONTEXT('USERENV','CON_NAME'),SYS_CONTEXT('USERENV','CON_ID') into con_name, con_id from dual;
      :CON_NAME := con_name;
      :CON_ID := con_id;
      if con_name = 'CDB$ROOT' then
         parent_id := 0;
      else
         begin
            execute immediate 'select SNAPSHOT_PARENT_CON_ID from v$pdbs' into parent_id;
         exception
            when no_data_found then
            parent_id := 0;
         end;
      end if;
      case
        WHEN con_id = 0 then :CON_TYPE := 'NONCDB';
        WHEN con_id = 1 then :CON_TYPE := 'CDB';
        WHEN con_id not in (0,1) and parent_id <> 0 then :CON_TYPE := 'PDB_SNAPSHOT';
        ELSE  :CON_TYPE := 'PDB';
      end case;
  else
      select 'NONE',0,'NONE' into :CON_NAME, :CON_ID, :CON_TYPE from dual;
  end if;
end;
