CREATE TABLESPACE TOOLS LOGGING DATAFILE SIZE 32M
    AUTOEXTEND ON NEXT 16M MAXSIZE UNLIMITED
    EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT AUTO;
CREATE TABLESPACE T_AUD LOGGING DATAFILE  SIZE 100M
    AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED
    EXTENT MANAGEMENT LOCAL  AUTOALLOCATE SEGMENT SPACE MANAGEMENT AUTO;
CREATE TABLESPACE I_AUD LOGGING DATAFILE SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT  AUTO;
CREATE TABLESPACE T_DICT LOGGING DATAFILE  SIZE 100M AUTOEXTEND ON NEXT 32M MAXSIZE UNLIMITED EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT  AUTO;
CREATE TABLESPACE I_DICT LOGGING DATAFILE  SIZE 100M AUTOEXTEND ON NEXT 32M MAXSIZE UNLIMITED EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT  AUTO ;
CREATE TABLESPACE I_USR DATAFILE
   SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED,
   SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED,
   SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED
   PERMANENT EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT AUTO;
CREATE TABLESPACE T_USR DATAFILE
  SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED,
  SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED,
  SIZE 100M AUTOEXTEND ON NEXT 128M MAXSIZE UNLIMITED
  PERMANENT EXTENT MANAGEMENT LOCAL AUTOALLOCATE SEGMENT SPACE MANAGEMENT AUTO;
