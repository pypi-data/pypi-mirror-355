import json,logging
from localstack.services.sns.models import SnsSubscription
from localstack.services.sns.publisher import PublishDispatcher,SnsBatchPublishContext,SnsPublishContext
from localstack.utils.patch import Patch
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.context import TraceContext,get_trace_context,set_trace_context,submit_with_trace_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import log_event_studio_error
LOG=logging.getLogger(__name__)
class SNSInstrumentation(Instrumentation):
	def apply(self):Patch.function(PublishDispatcher.publish_to_topic,self._publish_to_topic).apply();Patch.function(PublishDispatcher.publish_batch_to_topic,self._publish_to_topic).apply();Patch.function(PublishDispatcher._submit_notification,self._submit_sns_notification_with_context).apply()
	def _publish_to_topic(self,fn,self_,ctx:SnsPublishContext|SnsBatchPublishContext,topic_arn:str)->dict:
		B='Publish';A='message'
		try:
			trace_context=get_trace_context();parent_id=trace_context.parent_id;trace_id=trace_context.trace_id;version=trace_context.version;message=vars(ctx.message).copy();topic_attributes=ctx.topic_attributes.copy();topic_attributes.pop('sns_backend')
			try:message[A]=json.loads(json.loads(message[A]))
			except TypeError:
				try:message[A]=json.loads(message[A])
				except json.JSONDecodeError:pass
			except json.JSONDecodeError:pass
			input_event=InputEventModel(parent_id=parent_id,trace_id=trace_id,event_id=message['message_id'],version=version,account_id=ctx.store._account_id,region=ctx.store._region_name,service=ServiceName.SNS,resource_name=topic_attributes.get('name'),arn=topic_arn,operation_name=B,is_replayable=True,event_data={A:message},event_metadata={'topic_arn':topic_attributes.get('arn')});span_id,trace_id=self.event_service.store_event(InputEventModel.model_validate(input_event));new_trace_context=TraceContext(trace_id=trace_id,parent_id=span_id,version=version);set_trace_context(new_trace_context)
		except Exception as e:log_event_studio_error(logger=LOG,service=ServiceName.SNS,operation=B,error=str(e))
		return fn(self_,ctx=ctx,topic_arn=topic_arn)
	def _submit_sns_notification_with_context(self,fn,self_,notifier,ctx:SnsPublishContext,subscriber:SnsSubscription):return submit_with_trace_context(self_.executor,notifier.publish,ctx,subscriber)