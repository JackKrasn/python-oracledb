prompt
prompt Checking tablespaces

variable err_count number
declare
  names varchar2(100) := '&1';
  old_pos pls_integer;
  cur_pos pls_integer;
  name varchar2(100);
  was_empty boolean := false;
  checked_names varchar2(100) := ',';
  procedure check_tspace(name varchar2) is
    c number;
  begin
    if name is null then
      if was_empty then
        return;
      else
        was_empty := true;
        :err_count := :err_count + 1;
        dbms_output.put_line('Empty string used as tablespace name');
      end if;
    else
      if instr(checked_names, ',' || name || ',') > 0 then
        return;
      else
        checked_names := checked_names || name || ',';
      end if;
      select count(*) into c from user_tablespaces where tablespace_name = upper(name);
      if c <> 1 then
        :err_count := :err_count + 1;
        dbms_output.put_line('Tablespace ''' || name || ''' does not exist');
      end if;
    end if;
  end;
begin
  :err_count := 0;
  old_pos := 1;
  loop
    cur_pos := instr(names, ',', old_pos);
    if nvl(cur_pos, 0) = 0 then
      name := trim(substr(names, old_pos));
      check_tspace(name);
      return;
    end if;
    name := trim(substr(names, old_pos, cur_pos - old_pos));
    check_tspace(name);
    old_pos := cur_pos + 1;
  end loop;
end;
/

@@exit_when ':err_count > 0'
