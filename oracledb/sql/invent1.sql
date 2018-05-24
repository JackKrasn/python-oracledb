BEGIN   
   execute immediate 'create table keaparam tablespace SYSAUX as 
                         select log_mode, controlfile_type,open_mode, database_role from v$database';
    execute immediate 'alter table keaparam add
                          (job_queue_processes varchar2(20)';
   execute immediate 'insert into keaparam(job_queue_processes) select value from v$parameter where name=''job_queue_processes''';
   OPEN :cursor FOR 'select * from keaparam';
--   execute immediate 'drop table keaparam';
END; 
