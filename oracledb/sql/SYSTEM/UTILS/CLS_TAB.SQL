alter table METHOD_PARAMETERS add CRIT_ID varchar2(16);
alter table METHOD_PARAMETERS add CRIT_CLASS_ID varchar(16);

alter table METHOD_VARIABLES  add CRIT_ID varchar2(16);
alter table METHOD_VARIABLES  add CRIT_CLASS_ID varchar(16);

create index IDX_METHOD_PARAMS_CRIT_ID
  on METHOD_PARAMETERS(CRIT_ID)
  tablespace &&TSPACEI;

create index IDX_METHOD_VARS_CRIT_ID
  on METHOD_VARIABLES(CRIT_ID)
  tablespace &&TSPACEI;

alter table METHOD_PARAMETERS add constraint FK_METHOD_PARAMETERS_CRIT_ID
  foreign key(CRIT_ID) references CRITERIA(ID) on delete set null;

alter table METHOD_PARAMETERS add constraint FK_METHOD_PARAMS_CRIT_CLASS_ID
  foreign key(CRIT_CLASS_ID) references CLASSES(ID) on delete set null;

alter table METHOD_VARIABLES  add constraint FK_METHOD_VARIABLES_CRIT_ID
  foreign key(CRIT_ID) references CRITERIA(ID) on delete set null;

alter table METHOD_VARIABLES  add constraint FK_METHOD_VARS_CRIT_CLASS_ID
  foreign key(CRIT_CLASS_ID) references CLASSES(ID) on delete set null;

create index IDX_CONTROLS_CRIT_ID
  on CONTROLS(CRIT_ID)
  tablespace &&TSPACEI;

alter table class_tab_columns  add sequenced varchar2(30);

alter table class_tab_columns  add nt_table  varchar2(30);

alter table class_part_columns add nt_table  varchar2(30);

alter table class_indexes add qual varchar2(700);

create table class_rec_fields(
  CLASS_ID         VARCHAR2(16),
  QUAL             VARCHAR2(700),
  POSITION         NUMBER,
  FIELD            VARCHAR2(30),
  SELF_CLASS_ID    VARCHAR2(16),
  BASE_CLASS_ID    VARCHAR2(16),
  TARGET_CLASS_ID  VARCHAR2(16)
) tablespace &&tusers;

alter table class_rec_fields add constraint
  pk_cls_rec_flds_cls_id_qual primary key(class_id,qual)
  using index tablespace &&tspacei;

alter table class_rec_fields add constraint
  fk_cls_rec_fields_class_id foreign key(class_id)
  references classes(id) on delete cascade;

create table CURSORS
(
  METHOD_ID VARCHAR2(16),
  POSITION  NUMBER,
  PIECE     NUMBER,
  TEXT      VARCHAR2(2000)
)
tablespace &&TUSERS;

-- Create/Recreate primary, unique and foreign key constraints
alter table CURSORS
  add constraint PK_CURSORS primary key (METHOD_ID,POSITION,PIECE)
  using index
  tablespace &&TSPACEI;

alter table CURSORS
  add constraint FK_CURSORS_METHOD_ID foreign key (METHOD_ID)
  references METHODS (ID) on delete cascade;

alter table classes drop constraint CHK_CLASSES_BASE_CLASS_ID;

alter table classes add constraint CHK_CLASSES_BASE_CLASS_ID
CHECK(BASE_CLASS_ID IN ('STRING','NUMBER','DATE','BOOLEAN','MEMO','OLE','STRUCTURE','REFERENCE','COLLECTION','TABLE'));

alter table classes drop constraint CHK_CLASSES_AGREGATE;

alter table classes add has_type varchar2(1);

alter table classes modify has_type default '0';

update classes set has_type='0' where has_type is null;

update classes c set has_type='1' where exists
  (select 1 from classes t where t.base_class_id='TABLE' and t.target_class_id=c.id);

commit;

create type TYPE_STRING_TABLE  is table of varchar2(32767)
/
create type TYPE_MEMO_TABLE    is table of varchar2(4000)
/
create type TYPE_REFSTRING_TABLE  is table of varchar2(128)
/
create type TYPE_DEFSTRING_TABLE  is table of varchar2(256)
/
create type TYPE_BOOLSTRING_TABLE is table of varchar2(1)
/
create type TYPE_DATE_TABLE       is table of date
/
create type TYPE_NUMBER_TABLE     is table of number
/
create type TYPE_RAW_TABLE        is table of raw(2000)
/
create type TYPE_LONGRAW_TABLE    is table of raw(32767)
/
create type TYPE_BLOB_TABLE       is table of blob
/
create type TYPE_CLOB_TABLE       is table of clob
/
create type TYPE_BFILE_TABLE      is table of bfile
/
create type TYPE_TIMESTAMP_TABLE      is table of timestamp_unconstrained
/
create type TYPE_TIMESTAMP_TZ_TABLE   is table of timestamp_tz_unconstrained
/
create type TYPE_TIMESTAMP_LTZ_TABLE  is table of timestamp_ltz_unconstrained
/
create type TYPE_INTERVAL_TABLE       is table of dsinterval_unconstrained
/
create type TYPE_INTERVAL_YM_TABLE    is table of yminterval_unconstrained
/

create synonym TYPE_REFERENCE_TABLE for TYPE_NUMBER_TABLE
/

create synonym TYPE_LONG_TABLE for TYPE_STRING_TABLE
/

create synonym TYPE_LONG#RAW_TABLE for TYPE_LONGRAW_TABLE
/


