import logging
from localstack.aws.api.events import AccountId
from eventstudio.api.frontend_routes import FrontendRoutes
from eventstudio.api.v1.routes import V1ApiRoutes
from eventstudio.replay.replay import ReplayEventSender,ReplayEventSenderFactory
from eventstudio.services.error_service import ErrorService
from eventstudio.services.event_service import EventService
from eventstudio.services.event_streamer_service import EventStreamerService
from eventstudio.types.event import RegionName
from eventstudio.types.services import ServiceName
LOG=logging.getLogger(__name__)
class WebApp(FrontendRoutes,V1ApiRoutes):
	def __init__(A,event_service:EventService,error_service:ErrorService,event_streamer_service:EventStreamerService):A.event_service=event_service;A.error_service=error_service;A.event_streamer_service=event_streamer_service;(A._replay_event_sender_store):dict[tuple[ServiceName,AccountId,RegionName],ReplayEventSender]={}
	def _get_replay_event_sender(A,service:ServiceName,account_id:AccountId,region:RegionName)->ReplayEventSender:
		E=region;D=account_id;C=service;B=C,D,E
		if B not in A._replay_event_sender_store:LOG.debug(f"Creating new ReplayEventSender for {B}");F=ReplayEventSenderFactory(C,D,E,A.error_service).get_sender();A._replay_event_sender_store[B]=F
		return A._replay_event_sender_store[B]