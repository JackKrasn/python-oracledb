begin
   open :cursor for select name,sequence# from v$archived_log where status='A';
end;
