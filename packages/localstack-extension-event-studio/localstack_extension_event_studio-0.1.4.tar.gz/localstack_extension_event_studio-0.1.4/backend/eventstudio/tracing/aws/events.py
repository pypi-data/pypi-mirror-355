_J='region'
_I='account'
_H='detail-type'
_G='detail_type'
_F='event-bus-name'
_E='time'
_D='original_time'
_C='id'
_B='event_bus_name'
_A=None
import copy,logging
from localstack.aws.api import RequestContext
from localstack.aws.api.events import PutEventsRequestEntry,PutEventsResultEntryList
from localstack.services.events.models import FormattedEvent,Rule
from localstack.services.events.provider import EventsProvider,extract_event_bus_name,extract_region_and_account_id
from localstack.services.events.target import TargetSender,transform_event_with_target_input_path
from localstack.utils.aws.arns import event_bus_arn
from localstack.utils.patch import Patch
from localstack.utils.strings import long_uid
from localstack.utils.xray.trace_header import TraceHeader
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.context import TraceContext,get_trace_context,set_trace_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import compile_regex_patterns,convert_raw_entry,log_event_studio_error
LOG=logging.getLogger(__name__)
IGNORE_EVENT_BRIDGE_DETAIL_TYPE_PATTERS=compile_regex_patterns(['Parameter Store Change'])
class EventsInstrumentation(Instrumentation):
	def apply(A):Patch.function(EventsProvider._process_entry,A._patch_process_entry).apply();Patch.function(EventsProvider._proxy_capture_input_event,A._patch_proxy_capture_input_event).apply();Patch.function(EventsProvider._process_rules,A._patch_process_rules).apply();Patch.function(TargetSender.process_event,A._process_event).apply()
	def _patch_process_entry(P,fn,self_,entry:PutEventsRequestEntry,processed_entries:PutEventsResultEntryList,failed_entry_count:dict[str,int],context:RequestContext,**J)->_A:
		I=failed_entry_count;H=processed_entries;G=self_;C=context;A=entry
		if(Q:=A.get('DetailType')):
			if any(A.match(Q)for A in IGNORE_EVENT_BRIDGE_DETAIL_TYPE_PATTERS):return fn(G,A,H,I,C,**J)
		D=get_trace_context();K=D.parent_id;B=D.trace_id;E=D.version;L=A.copy();M=L.get('EventBusName','default');F=extract_event_bus_name(M);N,O=extract_region_and_account_id(M,C);R=event_bus_arn(F,O,N);S=convert_raw_entry(L);T=InputEventModel(parent_id=K,trace_id=B,event_id=str(long_uid()),version=E,account_id=O,region=N,service=ServiceName.EVENTS,resource_name=F,arn=R,operation_name='PutEvents',is_replayable=True,event_metadata={_B:F},event_data=S);U,B=P.event_service.store_event(InputEventModel.model_validate(T));V=TraceContext(trace_id=B,parent_id=U,version=E);set_trace_context(V);fn(G,A,H,I,C,**J);W=TraceContext(trace_id=B,parent_id=K,version=E);set_trace_context(W)
	def _patch_proxy_capture_input_event(H,fn,self_,event:FormattedEvent,trace_header:TraceHeader,region:str,account_id:str,**N)->_A:F=account_id;E=region;B=get_trace_context();I=B.parent_id;C=B.trace_id;G=B.version;A=event.copy();D=A.pop(_F);J=event_bus_arn(D,F,E);A[_G]=A.pop(_H,_A);A.pop(_I,_A);A.pop(_J,_A);K=InputEventModel(parent_id=I,trace_id=C,event_id=A.pop(_C),version=G,account_id=F,region=E,service=ServiceName.EVENTS,resource_name=D,arn=J,operation_name='Converted',is_replayable=True,event_metadata={_B:D,_D:A.pop(_E)},event_data=A);L,C=H.event_service.store_event(InputEventModel.model_validate(K));M=TraceContext(trace_id=C,parent_id=L,version=G);set_trace_context(M)
	def _patch_process_rules(J,fn,self_,rule:Rule,region:str,account_id:str,event_formatted:FormattedEvent,trace_header:TraceHeader,**K)->_A:H=event_formatted;C=account_id;B=region;E=get_trace_context();I=E.parent_id;D=E.trace_id;F=E.version;A=H.copy();G=A.pop(_F);C=A.pop(_I);B=A.pop(_J);L=event_bus_arn(G,C,B);A[_G]=A.pop(_H,_A);M=InputEventModel(parent_id=I,trace_id=D,event_id=A.pop(_C),version=F,account_id=C,region=B,service=ServiceName.EVENTS,resource_name=G,arn=L,operation_name='Match Rule',event_metadata={_B:G,_D:A.pop(_E)},event_data=A);N,D=J.event_service.store_event(InputEventModel.model_validate(M));O=TraceContext(trace_id=D,parent_id=N,version=F);set_trace_context(O);fn(self_,rule,B,C,H,trace_header,**K);P=TraceContext(trace_id=D,parent_id=I,version=F);set_trace_context(P)
	def _process_event(I,fn,self_,event:FormattedEvent,trace_header:TraceHeader,**S)->_A:
		U='Send to Target';R='replay-name';Q='replay_name';M=trace_header;L=event;E=self_
		try:
			N=get_trace_context();D=N.parent_id;V=copy.copy(D);B=N.trace_id;F=N.version;A=L.copy();C=A.pop(_F);J=A.pop(_I);K=A.pop(_J);O=event_bus_arn(C,J,K);A[_G]=A.pop(_H,_A)
			if(W:=E.target.get('InputPath')):P=transform_event_with_target_input_path(W,A);G=InputEventModel(parent_id=D,trace_id=B,event_id=A.pop(_C),version=F,account_id=J,region=K,service=ServiceName.EVENTS,resource_name=C,arn=O,operation_name='InputPathTransformation',event_metadata={_B:C,Q:A.get(R,_A),_D:A.pop(_E)},event_data=P);H,B=I.event_service.store_event(InputEventModel.model_validate(G));D=H
			if(X:=E.target.get('InputTransformer')):P=E.transform_event_with_target_input_transformer(X,A);G=InputEventModel(parent_id=D,trace_id=B,event_id=A.pop(_C),version=F,account_id=J,region=K,service=ServiceName.EVENTS,resource_name=C,arn=O,operation_name='InputTransformation',event_metadata={_B:C,Q:A.get(R,_A),_D:A.pop(_E)},event_data=P);H,B=I.event_service.store_event(InputEventModel.model_validate(G));D=H
			G=InputEventModel(parent_id=D,trace_id=B,event_id=A.pop(_C),version=F,account_id=J,region=K,service=ServiceName.EVENTS,resource_name=C,arn=O,operation_name=U,event_metadata={_B:C,Q:A.get(R,_A),_D:A.pop(_E)},event_data=A);H,B=I.event_service.store_event(InputEventModel.model_validate(G));T=TraceContext(trace_id=B,parent_id=H,version=F);set_trace_context(T)
			if(Y:=M.root):I.trace_link_service.store_trace_link(trace_link=Y,trace_context=T)
			fn(E,L,M,**S);Z=TraceContext(trace_id=B,parent_id=V,version=F);set_trace_context(Z)
		except Exception as a:log_event_studio_error(logger=LOG,service=ServiceName.EVENTS,operation=U,error=str(a));return fn(E,L,M,**S)