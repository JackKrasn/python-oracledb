prompt rebuilding objects,col2obj,collections views

exec after_install.create_diarys('1');

exec dbms_session.reset_package
exec executor.setnlsparameters

exec storage_mgr.verbose:=true
exec storage_mgr.pipe_name:='&&pipe_name'

exec storage_utils.verbose := true
exec storage_utils.pipe_name := '&&pipe_name'

begin
    for c in (
        select distinct class_id from class_partitions where partition_position is not null
    ) loop
        part_mgr.create_partition_views(c.class_id);
    end loop;
end;
/


exec storage_mgr.create_objects_view(true)

exec storage_mgr.create_collection_views(true,true)

alter package rtlobj compile body;




