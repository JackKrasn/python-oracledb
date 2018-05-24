DECLARE
   TYPE list_of_parameters IS TABLE OF v$parameter.value%TYPE INDEX BY varchar2(20);
   parameters list_of_parameters;
   vdat v$database%ROWTYPE;
   e_noTblFound EXCEPTION;
   e_notOpen EXCEPTION;
   PRAGMA exception_init(e_noTblFound, -942);          
   PRAGMA exception_init(e_notOpen, -1219);
   cIndex varchar2(20);   
BEGIN
   FOR par IN (select name,NVL(value,'NONE') as value from v$parameter where lower(name) in ('compatible','local_listener','job_queue_processes','spfile','db_create_file_dest'))
   LOOP
      parameters(par.name) := par.value;
   END LOOP;
     SELECT * INTO vdat from v$database;
   cIndex := parameters.FIRST;
   dbms_output.put_line('compatible:'||parameters('compatible')||
                        ';local_listener:'||parameters('local_listener')||
                        ';job_queue_processes:'||parameters('job_queue_processes')||
                        ';spfile:'||parameters('spfile')||
                        ';db_create_file_dest:'||parameters('db_create_file_dest')||                        
                        ';log_mode:'||vdat.log_mode||
			';open_mode:'||vdat.open_mode||
                        ';database_role:'||vdat.database_role);
END;
