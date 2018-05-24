begin
open :cursor for select name,value from v$parameter where name in ('local_listener', 'job_queue_processes', 'db_create_file_dest', 'spfile','db_recovery_file_dest');
end;

