_O='sqlalchemy.orm'
_N='sqlalchemy.dialects'
_M='sqlalchemy.pool'
_L='sqlalchemy.engine.Engine'
_K='sqlalchemy.engine'
_J='sqlalchemy'
_I='standard'
_H=None
_G=True
_F='propagate'
_E='WARNING'
_D='level'
_C='console'
_B=False
_A='handlers'
import logging.config
from typing import Optional
from sqlalchemy import create_engine,event,text
from sqlalchemy.engine import Engine
from eventstudio.db.models import Base
from eventstudio.db.utils import check_and_close_sqlite_db,get_database_directory
logging.config.dictConfig({'version':1,'disable_existing_loggers':_B,'formatters':{_I:{'format':'%(asctime)s %(levelname)s %(name)s: %(message)s'}},_A:{_C:{'class':'logging.StreamHandler','formatter':_I,_D:_E}},'loggers':{_J:{_A:[_C],_D:_E,_F:_B},_K:{_A:[_C],_D:_E,_F:_B},_L:{_A:[_C],_D:_E,_F:_B},_M:{_A:[_C],_D:_E,_F:_B},_N:{_A:[_C],_D:_E,_F:_B},_O:{_A:[_C],_D:_E,_F:_B}}})
logging.getLogger(_J).setLevel(logging.WARNING)
logging.getLogger(_K).setLevel(logging.WARNING)
logging.getLogger(_L).setLevel(logging.WARNING)
logging.getLogger(_M).setLevel(logging.WARNING)
logging.getLogger(_N).setLevel(logging.WARNING)
logging.getLogger(_O).setLevel(logging.WARNING)
LOG=logging.getLogger(__name__)
_GLOBAL_SYNC_DB_ENGINE:Optional[Engine]=_H
def _create_and_configure_engine(database_url:str,create_tables:bool=_G)->Engine:
	E='PRAGMA journal_mode=WAL;';A=database_url;LOG.info(f"Creating SQLAlchemy engine for URL: {A}")
	try:B=create_engine(A,echo=_G)
	except Exception as F:LOG.error(f"Failed to create database engine for {A}: {F}",exc_info=_G);raise
	def G(dbapi_connection,connection_record):
		try:A=dbapi_connection.cursor();A.execute(E);B=A.fetchone();LOG.debug(f"PRAGMA journal_mode=WAL result: {B}");A.close();LOG.info('WAL mode set for new SQLite connection via event listener.')
		except Exception as C:LOG.error(f"Failed to set WAL mode via event listener: {C}",exc_info=_G)
	if B.dialect.name=='sqlite':
		event.listen(B.pool,'connect',G);LOG.info(f"WAL mode event listener attached to SQLite engine for: {A}")
		try:
			with B.connect()as D:
				C=D.execute(text('PRAGMA journal_mode;')).scalar_one_or_none()
				if C and C.lower()!='wal':D.execute(text(E));D.commit();LOG.info(f"Initial PRAGMA journal_mode=WAL executed directly for: {A}")
				elif C:LOG.info(f"Initial journal_mode for {A} already set to: {C}")
		except Exception as H:LOG.warning(f"Could not directly verify/set initial WAL mode for {A} (listener should still work): {H}")
	if create_tables:LOG.info(f"Creating database tables for: {A}");Base.metadata.create_all(B)
	LOG.info(f"Successfully configured engine for: {A}");return B
def initialize_db_engine()->Engine:
	global _GLOBAL_SYNC_DB_ENGINE
	if _GLOBAL_SYNC_DB_ENGINE is not _H:LOG.warning('Production engine already initialized.');return _GLOBAL_SYNC_DB_ENGINE
	A=get_database_directory();check_and_close_sqlite_db(A);B=f"sqlite:///{A}"
	try:_GLOBAL_SYNC_DB_ENGINE=_create_and_configure_engine(B);LOG.info(f"Production synchronous database engine initialized: {B}");return _GLOBAL_SYNC_DB_ENGINE
	except Exception as C:LOG.critical(f"CRITICAL: Failed to initialize production database engine: {C}",exc_info=_G);raise RuntimeError('Failed to initialize production database engine. Application cannot proceed.')from C
def get_sync_db_engine()->Engine:
	if _GLOBAL_SYNC_DB_ENGINE is _H:LOG.critical('Production database engine (PROD_SYNC_ENGINE) is not initialized!');raise RuntimeError('Production database engine has not been initialized. Application cannot proceed.')
	return _GLOBAL_SYNC_DB_ENGINE
def dispose_sync_db_engine():
	global _GLOBAL_SYNC_DB_ENGINE
	if _GLOBAL_SYNC_DB_ENGINE:
		try:_GLOBAL_SYNC_DB_ENGINE.dispose();LOG.info('Production synchronous database engine disposed.');_GLOBAL_SYNC_DB_ENGINE=_H
		except Exception as A:LOG.error(f"Error disposing production synchronous database engine: {A}",exc_info=_G)