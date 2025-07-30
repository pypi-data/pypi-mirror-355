from localstack.aws.api.events import AccountId
from localstack.aws.connect import InternalClientFactory,connect_to
from eventstudio.context import AppContext
from eventstudio.services.error_service import ErrorService
from eventstudio.services.event_service import EventService
from eventstudio.services.trace_link_service import TraceLinkService
from eventstudio.types.event import RegionName
class Instrumentation:
	app_context:AppContext
	def __init__(A,app_context:AppContext):A._app_context=app_context;(A._clients):dict[tuple[AccountId,RegionName],InternalClientFactory]={}
	@property
	def event_service(self)->EventService:return self._app_context.event_service
	@property
	def error_service(self)->ErrorService:return self._app_context.error_service
	@property
	def trace_link_service(self)->TraceLinkService:return self._app_context.trace_link_service
	def apply(A):0
	def client(B,account_id,region)->InternalClientFactory:
		D=region;C=account_id;E=C,D;A=B._clients.get(E)
		if A is None:A=connect_to(region_name=D,aws_access_key_id=C);B._clients[E]=A
		return A