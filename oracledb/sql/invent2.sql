SELECT name,NVL(value,'NONE') as value from v$parameter
   where lower(name) in ('compatible','local_listener','job_queue_processes','spfile','db_create_file_dest');
