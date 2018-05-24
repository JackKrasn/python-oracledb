--audm.sql
def AUDM_OWNER='AUDM' --Schema Name for AUDIT manager

--init1.sql
def INIT_TDEF='T_USR' --Default tablespace
def INIT_TTMP='TEMP' --Temporary tablespace

--audm.sql and init1.sql
def IBSO_OWNER='IBS' --IBSO schema owner name

/**
 * You CAN redefine DEFAULT TABLESPACE NAMES in
 * FILE usr_sets.sql. IF you going to do this
 * PUT usr_sets.sql in upgrade ROOT directory.
 * As EXAMPLE use ABOVE part of settings.sql
 */
SET TERMOUT OFF
@@usr_sets
SET TERMOUT ON

SET SERVEROUTPUT ON SIZE 100000
SET VERIFY OFF
