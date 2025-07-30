_B='EventStudioContext not ready for _get_client_post_hook_with_trace_header. Error highlighting might fail.'
_A=None
import logging,typing as t
from typing import Any
from botocore.client import BaseClient
from localstack.aws import handlers
from localstack.aws.api import RequestContext
from localstack.aws.chain import HandlerChain
from localstack.aws.connect import InternalClientFactory
from localstack.aws.gateway import Gateway
from localstack.aws.handlers.cors import ALLOWED_CORS_ORIGINS
from localstack.config import is_in_docker
from localstack.extensions.patterns.webapp import WebAppExtension
from localstack.http import Response
from localstack.runtime import get_current_runtime
from localstack.utils.patch import Patch
from eventstudio.api.webapp import WebApp
from eventstudio.constants import INTERNAL_REQUEST_TRACE_HEADER
from eventstudio.context import get_app_context,initialize_app_context,shutdown_app_context
from eventstudio.db.utils import clear_db
from eventstudio.tracing.aws.apigateway import ApigatewayInstrumentation
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.aws.dynamodb import DynamoDBInstrumentation
from eventstudio.tracing.aws.events import EventsInstrumentation
from eventstudio.tracing.aws.iam import IAMInstrumentation
from eventstudio.tracing.aws.lambda_ import LambdaInstrumentation
from eventstudio.tracing.aws.s3 import S3Instrumentation
from eventstudio.tracing.aws.sns import SNSInstrumentation
from eventstudio.tracing.aws.sqs import SQSInstrumentation
from eventstudio.tracing.context import extract_trace_context_from_context,get_trace_context,pop_request_context,push_request_context,set_trace_context
from eventstudio.tracing.initial_call_handler import EventStudioInitialCallHandler
from eventstudio.tracing.logging_handler import EventStudioLogHandler
from eventstudio.tracing.xray_tracing import get_trace_context_from_xray_trace_header
from eventstudio.types.error import ErrorType,InputErrorModel
LOG=logging.getLogger(__name__)
class MyExtension(WebAppExtension):
	name='eventstudio';aws_instrumentations:list[t.Type[Instrumentation]]=[ApigatewayInstrumentation,DynamoDBInstrumentation,EventsInstrumentation,IAMInstrumentation,LambdaInstrumentation,S3Instrumentation,SNSInstrumentation,SQSInstrumentation]
	def __init__(A):
		super().__init__(template_package_path=_A)
		if not is_in_docker:ALLOWED_CORS_ORIGINS.append('http://127.0.0.1:3000')
		clear_db()
	def set_thread_local_trace_parameters_from_context(D,_chain:HandlerChain,context:RequestContext,_response:Response):
		B=context
		try:C=get_app_context()
		except RuntimeError:LOG.error(_B)
		A=extract_trace_context_from_context(B)
		if A.parent_id is _A:
			A=get_trace_context_from_xray_trace_header(B.get('trace_context'),C.trace_link_service)
			if A is _A or A.parent_id is _A:A=get_trace_context()
		set_trace_context(A)
	def _get_client_post_hook_with_trace_header(G,fn,self_,client:BaseClient,**C):
		B=self_;A=client
		try:D=get_app_context()
		except RuntimeError:LOG.error(_B);return fn(B,client=A,**C)
		A.meta.events.register('before-call.*.*',handler=_handler_inject_trace_header);E=D.error_service
		def F(exception,**F):
			A=exception
			if A is not _A:
				C=get_trace_context();B=C.parent_id
				if B is not _A:D=InputErrorModel(error_type=ErrorType.BOTO_ERROR,error_message=str(A),span_id=B);E.store_error(D)
		A.meta.events.register('after-call-error',handler=F);return fn(B,client=A,**C)
	def _inject_request_context_handlers(D,gateway:Gateway):
		A=gateway
		def B(_chain:HandlerChain,context:RequestContext,_response:Response):push_request_context(context)
		def C(_chain:HandlerChain,_context:RequestContext,_response:Response):pop_request_context()
		A.request_handlers.insert(0,B);A.finalizers.append(C)
	def on_platform_start(B):
		super().on_platform_start();LOG.info('EventStudio MyExtension: Platform starting creating app context')
		try:clear_db();LOG.info('Database cleared.');initialize_app_context()
		except RuntimeError as A:LOG.critical(f"EventStudio: CRITICAL - Failed to initialize EventStudioContext: {A}. Extension may not function.");return
		except Exception as A:LOG.critical(f"EventStudio: CRITICAL - Unexpected error during context initialization or DB clear: {A}",exc_info=True);return
	def on_platform_ready(A):
		super().on_platform_ready();LOG.info('EventStudio MyExtension: Platform ready. Initializing services...');B=get_app_context()
		for D in A.aws_instrumentations:D(app_context=B).apply()
		A._inject_request_context_handlers(get_current_runtime().components.gateway);handlers.serve_custom_service_request_handlers.append(A.set_thread_local_trace_parameters_from_context);Patch.function(InternalClientFactory._get_client_post_hook,A._get_client_post_hook_with_trace_header).apply();E=EventStudioInitialCallHandler(event_service=B.event_service);handlers.serve_custom_service_request_handlers.append(E);C=EventStudioLogHandler(error_service=B.error_service);C.setLevel(logging.INFO);F=logging.getLogger();F.addHandler(C);LOG.info('Extension Loaded')
	def collect_routes(C,routes:list[t.Any]):
		LOG.info('EventStudio: Collecting routes...')
		try:A=get_app_context();routes.append(WebApp(event_service=A.event_service,error_service=A.error_service,event_streamer_service=A.event_streamer_service));LOG.info('EventStudio WebApp routes collected.')
		except RuntimeError as B:LOG.critical(f"EventStudio: Cannot collect routes because EventStudioContext is not initialized: {B}")
		except Exception as B:LOG.error(f"EventStudio: Error during route collection: {B}",exc_info=True)
	def on_platform_shutdown(A):LOG.info('EventStudio: Extension shutting down...');shutdown_app_context();LOG.info('EventStudio: Shutdown complete.')
def _handler_inject_trace_header(params:dict[str,Any],context:dict[str,Any],**B):
	A=get_trace_context()
	if A.trace_id and A.parent_id:params['headers'][INTERNAL_REQUEST_TRACE_HEADER]=A.json()