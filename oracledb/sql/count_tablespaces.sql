begin
open :cursor for select vt.name,count(vd.file#) cnt from v$datafile vd 
                            inner join v$tablespace vt on vd.ts#=vt.ts# 
                            where vt.name not in ('SYSTEM','SYSAUX','XDB','UNDO','UNDOTBS1') group by vt.name order by cnt;

end;