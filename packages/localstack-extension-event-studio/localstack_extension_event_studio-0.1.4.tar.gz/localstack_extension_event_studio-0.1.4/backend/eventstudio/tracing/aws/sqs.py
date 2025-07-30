import logging
from localstack.aws.api.sqs import Message
from localstack.services.sqs.models import FifoQueue,StandardQueue
from localstack.utils.patch import Patch
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.context import TraceContext,get_request_context,get_trace_context,set_trace_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import is_lambda_helper_queue,load_sqs_message_body,log_event_studio_error,pars_timestamp_ms
LOG=logging.getLogger(__name__)
class SQSInstrumentation(Instrumentation):
	def apply(A):Patch.function(StandardQueue.put,A._put_message_sqs_queue).apply();Patch.function(FifoQueue.put,A._put_message_sqs_queue).apply()
	def _put_message_sqs_queue(F,fn,self_,message:Message,**L)->dict:
		G=message;A=self_
		try:C=get_trace_context();M=C.parent_id;D=C.trace_id;H=C.version;E=G.copy();N,O=load_sqs_message_body(E['Body']);P=pars_timestamp_ms(list(E['Attributes'].values())[1]);I=get_request_context();J=I.account_id;K=I.region;B=is_lambda_helper_queue(A.arn,F.client(J,K).lambda_);Q=f"https://sqs.{K}.localhost.localstack.cloud:4566/{J}/{A.name}";R=InputEventModel(parent_id=M,trace_id=D,event_id=E.pop('MessageId'),version=H,account_id=A.account_id,region=A.region,service=ServiceName.SQS,resource_name=A.name,arn=A.arn,operation_name='SendMessage',is_replayable=B if B else True,is_hidden=B if B else False,event_data={'body':N},event_metadata={'queue_arn':A.arn,'body_type':O,'original_time':P,'queue_url':Q});S,D=F.event_service.store_event(InputEventModel.model_validate(R));T=TraceContext(trace_id=D,parent_id=S,version=H);set_trace_context(T)
		except Exception as U:log_event_studio_error(logger=LOG,service=ServiceName.SQS,operation='Send',error=str(U))
		return fn(A,message=G,**L)