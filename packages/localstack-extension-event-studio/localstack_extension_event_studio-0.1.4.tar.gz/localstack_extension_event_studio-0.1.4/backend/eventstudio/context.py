_A=None
import logging
from typing import Optional
from sqlalchemy.engine import Engine
from eventstudio.db.connection import dispose_sync_db_engine,initialize_db_engine
from eventstudio.services.error_service import ErrorService
from eventstudio.services.event_service import EventService
from eventstudio.services.event_streamer_service import EventStreamerService
from eventstudio.services.trace_link_service import TraceLinkService
from eventstudio.storage.error_repository import ErrorRepository
from eventstudio.storage.event_repository import EventRepository
from eventstudio.storage.trace_link_repository import TraceLinkRepository
LOG=logging.getLogger(__name__)
class AppContext:
	db_engine:Engine;event_streamer_service:EventStreamerService;event_repository:EventRepository;error_repository:ErrorRepository;trace_link_repository:TraceLinkRepository;event_service:EventService;error_service:ErrorService;trace_link_service:TraceLinkService
	def __init__(A,db_engine:Engine):(A._db_engine):Engine=db_engine;(A._event_streamer_service):EventStreamerService=EventStreamerService();A._event_repository=EventRepository(engine=A._db_engine);A._error_repository=ErrorRepository(engine=A._db_engine);A._trace_link_repository=TraceLinkRepository(engine=A._db_engine);A._event_service=EventService(event_repository=A._event_repository,event_streamer_service=A._event_streamer_service);A._error_service=ErrorService(error_repository=A._error_repository);A._trace_link_service=TraceLinkService(trace_link_repository=A._trace_link_repository);LOG.info('AppContext container initialized with all services.')
	@property
	def event_streamer_service(self)->EventStreamerService:return self._event_streamer_service
	@property
	def event_service(self)->EventService:return self._event_service
	@property
	def error_service(self)->ErrorService:return self._error_service
	@property
	def trace_link_service(self)->TraceLinkService:return self._trace_link_service
	def clear_all_data(A):
		LOG.warning('Clearing all event and error data from the database.')
		try:B=A.event_repository.delete_all_events();C=A.error_repository.delete_all_errors();D=A.trace_link_repository.delete_all_trace_links();LOG.info(f"Data cleared: {B} events, {C} errors, {D} trace links.")
		except Exception as E:LOG.error(f"Error during clear_all_data: {E}",exc_info=True)
	def shutdown(A):LOG.info('Shutting down AppContext container.');A._event_streamer_service.close();A._db_engine.dispose()
_GLOBAL_APP_CONTEXT:Optional[AppContext]=_A
def initialize_app_context()->AppContext:
	global _GLOBAL_APP_CONTEXT
	if _GLOBAL_APP_CONTEXT is not _A:LOG.warning('AppContext already initialized. Skipping re-initialization.');return _GLOBAL_APP_CONTEXT
	LOG.info('Initializing AppContext container...');A:Optional[Engine]=_A
	try:
		A=initialize_db_engine()
		if A is _A:raise RuntimeError('Database engine is None, cannot initialize AppContext.')
		_GLOBAL_APP_CONTEXT=AppContext(db_engine=A);LOG.info('AppContext container initialized successfully.');return _GLOBAL_APP_CONTEXT
	except Exception as B:LOG.critical(f"Failed to initialize AppContext container: {B}",exc_info=True);_GLOBAL_APP_CONTEXT=_A;raise RuntimeError(f"Critical failure during AppContext initialization: {B}")
def get_app_context()->AppContext:
	if _GLOBAL_APP_CONTEXT is _A:LOG.error('Attempted to access AppContext before initialization or after a failed initialization.');raise RuntimeError('Application services are not available. Ensure initialize_app_context() was called successfully.')
	return _GLOBAL_APP_CONTEXT
def shutdown_app_context():
	global _GLOBAL_APP_CONTEXT
	if _GLOBAL_APP_CONTEXT is not _A:
		LOG.info('Shutting down AppContext and associated resources...')
		try:_GLOBAL_APP_CONTEXT.shutdown()
		except Exception as A:LOG.error(f"Error during AppContext.shutdown() method: {A}",exc_info=True)
		dispose_sync_db_engine();_GLOBAL_APP_CONTEXT=_A;LOG.info('AppContext shut down and DB engine disposed.')
	else:LOG.info('AppContext was not initialized; no shutdown actions needed.')