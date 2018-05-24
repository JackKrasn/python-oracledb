DECLARE
   oracle_version v$instance.version%TYPE;
   short_ov v$instance.version%TYPE;
   edition v$instance.edition%TYPE;
   cft_owner varchar2(20);
   kernel_version varchar2(20);
   query varchar2(4000);
   nls varchar2(30);
   psu varchar2(100);
   ojvm varchar2(50);
   db_name varchar2(20);
   no_such_table exception;
   pragma exception_init(no_such_table, -942 );
   cursor c1 (cft_owner varchar2) is
   SELECT   df.tablespace_name ctsname, round(SUM (df.BYTES) / 1024 / 1024,2) size_mb,
         round(SUM (df.BYTES) / 1024 / 1024 - fs.sum_free / 1024 / 1024, 2) size_used_mb,
         round(fs.sum_free / 1024 / 1024, 2) size_free_mb
    FROM dba_data_files df,
         (SELECT   tablespace_name, SUM (BYTES) sum_free
              FROM dba_free_space
          GROUP BY tablespace_name) fs,
         (SELECT DISTINCT a.tsn
                     FROM (SELECT DISTINCT tablespace_name tsn
                                      FROM dba_tables
                                     WHERE owner = upper(cft_owner)
                           UNION ALL
                           SELECT DISTINCT tablespace_name tsn
                                      FROM dba_indexes
                                     WHERE owner = upper(cft_owner)
                           UNION ALL
                           SELECT DISTINCT tablespace_name tsn
                                      FROM dba_lobs
                                     WHERE owner = upper(cft_owner)
                                     and tablespace_name not in (select tablespace_name
                                                                 from dba_tablespaces
                                                                 where contents='TEMPORARY')
                           ) a
          ) tsa
   WHERE df.tablespace_name = fs.tablespace_name(+)
         AND df.tablespace_name = tsa.tsn
   GROUP BY df.tablespace_name, fs.sum_free
                ORDER BY df.tablespace_name;
BEGIN
   select version,edition into oracle_version,edition from v$instance;
   select substr(version,0,2) into short_ov from v$instance;
   if short_ov = '11'
   then
      query :=  'select nvl((select comments from sys.registry$history where action_time=(select max(action_time) from sys.registry$history where bundle_series=''PSU'' and action=''APPLY'')) ,
                            ''None'') as vers from dual';
      execute immediate query into psu;
      --query:= ''
   elsif short_ov  = '12'
    then
      query := 'select nvl((
                             SELECT version || ''.'' || bundle_id ||'' - '' || description AS ver
                             FROM dba_registry_sqlpatch where flags = ''NB''
                             AND patch_uid IN (SELECT patch_uid FROM dba_registry_sqlpatch WHERE action = ''APPLY''
                                               MINUS
                                               SELECT patch_uid  FROM dba_registry_sqlpatch  WHERE action = ''ROLLBACK''
                                              )
                             AND action_time =
                             (SELECT MAX (action_time)  FROM dba_registry_sqlpatch WHERE action IN (''APPLY'', ''ROLLBACK'') AND flags = ''NB'')
                            ) ,''None'') as vers from dual';
      execute immediate query into psu;
   end if;
   begin
       execute immediate 'select value from audm.settings where name=''OWNERS''' into cft_owner;
   exception
       when no_such_table then
       cft_owner := 'None';
   end;
   select value into nls from v$nls_parameters where parameter='NLS_CHARACTERSET';
   if cft_owner = 'None' then
       kernel_version := 0;
   else
       query :='select '||cft_owner||'.inst_info.get_version from dual';
       execute immediate query into kernel_version;
   end if;
   select sys_context('USERENV','DB_UNIQUE_NAME') into db_name from dual;
   dbms_output.put_line('Oracle version:'||oracle_version);
   dbms_output.put_line('PSU:'||psu);
   dbms_output.put_line('NLS_CHARACTERSET:'||nls);
   dbms_output.put_line('DB_NAME:'||db_name);
   dbms_output.put_line('Edition:'||edition);
   dbms_output.put_line('Found owner:'||cft_owner);
   dbms_output.put_line('Kernel version:'||kernel_version);
   FOR tab in c1(cft_owner)
   LOOP
      dbms_output.put_line('  '||tab.ctsname||': '||tab.size_used_mb);
   END LOOP;
END;