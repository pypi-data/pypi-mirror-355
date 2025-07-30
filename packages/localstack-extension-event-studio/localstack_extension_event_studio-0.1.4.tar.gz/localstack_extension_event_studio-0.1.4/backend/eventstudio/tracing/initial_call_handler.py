_A='PutObject'
import logging
from localstack.aws.api import RequestContext
from localstack.aws.chain import HandlerChain
from localstack.http import Response
from eventstudio.services.event_service import EventService
from eventstudio.tracing.context import TraceContext,get_trace_context,set_trace_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import SERVICE_NAME_VALUES,ServiceName
from eventstudio.utils.utils import get_service_name,log_event_studio_error
LOG=logging.getLogger(__name__)
SERVICE_OPERATIONS_TO_CAPTURE_BY_SERVICE={ServiceName.EVENTS.value:['PutEvents'],ServiceName.DYNAMODB.value:['PutItem'],ServiceName.LAMBDA.value:['Invoke'],ServiceName.S3.value:[_A],ServiceName.SNS.value:['Publish'],ServiceName.SQS.value:['SendMessage']}
def skip_specific_operations(context:RequestContext)->bool:
	A=context;C=A.service.service_name;D=A.service_operation.operation
	if C==ServiceName.S3.value and D==_A:
		B=A.service_request.get('Bucket')
		if B and B.startswith('awslambda')and B.endswith('tasks'):return True
	return False
def is_request_from_lambda(context:RequestContext)->bool:
	B=context.request.environ['HTTP_USER_AGENT'];C=B.split();A=False
	for D in C:
		if D.startswith('exec-env/AWS_Lambda'):A=True;break
	return A
class EventStudioInitialCallHandler:
	def __init__(A,event_service:EventService):A._event_service=event_service
	def __call__(L,chain:HandlerChain,context:RequestContext,response:Response):
		K='service';B=None;A=context;C=getattr(getattr(A,K,B),'service_name',B);D=getattr(getattr(A,'service_operation',B),'operation',B)
		if C in SERVICE_NAME_VALUES and D in SERVICE_OPERATIONS_TO_CAPTURE_BY_SERVICE.get(C,[])and not skip_specific_operations(A):
			try:
				F=get_trace_context();M=F.parent_id;E=F.trace_id;G=0
				if(not A.is_internal_call or(M is B or E is B))and not is_request_from_lambda(A):
					if A.is_internal_call:H=ServiceName.INTERNAL;N=get_service_name(C);I='internal';J={K:N,'operation_name':D}
					else:H=ServiceName.EXTERNAL;I='external';J={'user_agent':A.request.user_agent.string,'browser':A.request.user_agent.browser,'language':A.request.user_agent.language,'platform':A.request.user_agent.platform,'version':A.request.user_agent.version}
					O=InputEventModel(parent_id=B,trace_id=B,event_id=A.request_id,version=G,account_id=A.account_id,region=A.region,service=H,resource_name=I,arn='not_applicable',operation_name=D,event_metadata=J);P,E=L._event_service.store_event(InputEventModel.model_validate(O));Q=TraceContext(trace_id=E,parent_id=P,version=G);set_trace_context(Q)
			except Exception as R:log_event_studio_error(logger=LOG,service=get_service_name(C),operation='InitialCall',error=str(R))