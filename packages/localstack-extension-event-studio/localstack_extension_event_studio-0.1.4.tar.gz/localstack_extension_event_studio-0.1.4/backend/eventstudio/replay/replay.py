_A=None
import json
from abc import ABC,abstractmethod
from datetime import datetime
from botocore.client import BaseClient
from localstack.aws.api.events import AccountId,PutEventsRequestEntry,PutEventsResponse
from localstack.aws.connect import connect_to
from eventstudio.constants import INTERNAL_REQUEST_TRACE_HEADER
from eventstudio.services.error_service import ErrorService
from eventstudio.tracing.context import TraceContext
from eventstudio.types.error import ErrorType,InputErrorModel
from eventstudio.types.event import EventModel,RegionName
from eventstudio.types.services import ServiceName
from eventstudio.utils.arns import get_queue_url_from_arn
from eventstudio.utils.utils import dict_to_xml
class ReplayEventSender(ABC):
	service:ServiceName;account_id:AccountId;region:RegionName
	def __init__(A,service:ServiceName,account_id:AccountId,region:RegionName,error_service:ErrorService):A.service=service;A.account_id=account_id;A.region=region;(A._client):BaseClient|_A=_A;(A._error_service):ErrorService=error_service
	@property
	def client(self):
		A=self
		if A._client is _A:A._client=A._initialize_client()
		return A._client
	def _initialize_client(A)->BaseClient:C=connect_to(aws_access_key_id=A.account_id,region_name=A.region);B=C.get_client(A.service.value);A._trace_header_virtual_parameter_hook(B);return B
	def _trace_header_virtual_parameter_hook(A,client:BaseClient):
		B=client
		def C(params,context,**B):
			A=params.pop('TraceContext',_A)
			if A is _A:return
			context[INTERNAL_REQUEST_TRACE_HEADER]=A.model_dump_json()
		def D(params,context,**B):
			if(A:=context.pop(INTERNAL_REQUEST_TRACE_HEADER,_A)):params['headers'][INTERNAL_REQUEST_TRACE_HEADER]=A
		B.meta.events.register(f"provide-client-params.{A.service.value}.*",C);B.meta.events.register(f"before-call.{A.service.value}.*",D)
	def _error_handling_hook(B,client:BaseClient,span_id:str):
		def A(exception,**D):
			A=exception
			if A is not _A:C=InputErrorModel(error_type=ErrorType.BOTO_ERROR,error_message=str(A),span_id=span_id);B._error_service.store_error(C)
		client.meta.events.register('after-call-error',handler=A)
	def replay_event(A,event:EventModel,trace_context:TraceContext)->dict[str,str]:B=event;A._error_handling_hook(A.client,B.span_id);return A.send_event(B,trace_context)
	@abstractmethod
	def send_event(self,event:EventModel,trace_context:TraceContext)->dict[str,str]:0
class DynamoDBReplayEventSender(ReplayEventSender):
	def send_event(B,event:EventModel,trace_context:TraceContext)->dict[str,str]:A=event;C=A.event_data;D=A.event_metadata;E=D.table_name;F=C.item;G=B.client.put_item(TableName=E,Item=F,TraceContext=trace_context);return G
class EventsReplayEventSender(ReplayEventSender):
	def _re_format_event(E,event:EventModel)->PutEventsRequestEntry:
		B=event;A=B.event_data;D=B.event_metadata;C={'Source':A.source,'DetailType':A.detail_type,'Detail':json.dumps(A.detail),'Time':B.creation_time.isoformat()if B.creation_time else datetime.now().isoformat(),'EventBusName':D.event_bus_name}
		if A.resources:C['Resources']=str(A.resources)
		if D.replay_name:C['ReplayName']=A.replay_name
		return PutEventsRequestEntry(**C)
	def send_event(A,event:EventModel,trace_context:TraceContext)->PutEventsResponse:B=A._re_format_event(event);C=A.client.put_events(Entries=[B],TraceContext=trace_context);return C
class LambdaReplayEventSender(ReplayEventSender):
	def send_event(B,event:EventModel,trace_context:TraceContext)->dict[str,str]:A=event;C=A.event_metadata.function_name;D=A.event_data.payload;E=A.event_metadata.invocation_type;F=B.client.invoke(FunctionName=C,InvocationType=E,Payload=json.dumps(D),TraceContext=trace_context);return F
class SnsReplayEventSender(ReplayEventSender):
	def send_event(B,event:EventModel,trace_context:TraceContext)->dict[str,str]:A=event;C=A.event_metadata.topic_arn;D=A.event_data.message.get('message');E=B.client.publish(TopicArn=C,Message=json.dumps(D),TraceContext=trace_context);return E
class SqsReplayEventSender(ReplayEventSender):
	def send_event(D,event:EventModel,trace_context:TraceContext)->dict[str,str]:
		A=event;E=get_queue_url_from_arn(A.event_metadata.queue_arn);B=A.event_data.body
		if A.event_metadata.body_type=='TEXT':C=B
		if A.event_metadata.body_type=='JSON':C=json.dumps(B)
		if A.event_metadata.body_type=='XML':C=dict_to_xml(B)
		F=D.client.send_message(QueueUrl=E,MessageBody=C,TraceContext=trace_context);return F
class S3ReplayEventSender(ReplayEventSender):
	def _get_object_version(A,bucket_name,key,version_id)->bytes:
		try:B=A.client.get_object(Bucket=bucket_name,Key=key,VersionId=version_id);return B['Body'].read()
		except Exception as C:return str(C)
	def send_event(B,event:EventModel,trace_context:TraceContext)->dict[str,str]:A=event.event_metadata;C=A.bucket;D=A.key;E=A.version_id;F=B._get_object_version(C,D,E);G=B.client.put_object(Bucket=C,Key=D,Body=F,TraceContext=trace_context);return G
class ReplayEventSenderFactory:
	service:ServiceName;account_id:AccountId;region:RegionName;service_map={ServiceName.DYNAMODB:DynamoDBReplayEventSender,ServiceName.EVENTS:EventsReplayEventSender,ServiceName.LAMBDA:LambdaReplayEventSender,ServiceName.SNS:SnsReplayEventSender,ServiceName.SQS:SqsReplayEventSender,ServiceName.S3:S3ReplayEventSender}
	def __init__(A,service:ServiceName,account_id:AccountId,region:RegionName,error_service:ErrorService):A.service=service;A.account_id=account_id;A.region=region;(A.error_service):ErrorService=error_service
	def get_sender(A)->ReplayEventSender:return A.service_map[A.service](service=A.service,account_id=A.account_id,region=A.region,error_service=A.error_service)