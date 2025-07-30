_C='DELETE'
_B='GET'
_A='error'
import logging,botocore.exceptions
from localstack.http import Request,route
from eventstudio import config
from eventstudio.tracing.context import TraceContext
from eventstudio.types.error import ErrorType,InputErrorModel
from eventstudio.types.event import EventModel,EventModelList,InputEventModel,InputEventModelList
from eventstudio.types.requests import DeleteEventsRequest
from eventstudio.types.responses import AddEventsResponse,DeleteAllErrorsResponse,DeleteAllEventsResponse,DeleteEventsResponse,GetEventResponse,ListErrorsResponse,ListEventsResponse,ReplayEventsResponse,TraceGraphResponse
from eventstudio.utils.utils import parse_request_body
LOG=logging.getLogger(__name__)
class V1ApiRoutes:
	@route(config.get_relative_url(config.EVENTS),methods=['WEBSOCKET'])
	def live_stream(self,request:Request,*args,**kwargs):return self.event_streamer_service.on_websocket_request(request,*args,**kwargs)
	@route(config.get_relative_url(config.EVENTS),methods=['POST'])
	def add_events(self,request:Request)->AddEventsResponse:
		events_input:InputEventModelList=parse_request_body(request,InputEventModelList);failed_entry_count=0;failed_entries=[]
		for event_data in events_input.events:
			response=self.event_service.store_event(event_data)
			if isinstance(response,dict)and _A in response:failed_entry_count+=1;failed_entries.append(response[_A])
		if failed_entry_count>0:return AddEventsResponse(status=400,FailedEntryCount=failed_entry_count,FailedEntries=failed_entries)
		return AddEventsResponse(status=200,FailedEntryCount=0,FailedEntries=[])
	@route(config.get_relative_url(config.EVENTS),methods=[_C])
	def delete_events(self,request:Request)->DeleteEventsResponse:
		body:DeleteEventsRequest=parse_request_body(request,DeleteEventsRequest);failed_entry_count=0;failed_entries=[]
		for span_id in body.span_ids:
			response=self.event_service.delete_event(span_id=span_id)
			if response:failed_entry_count+=1;failed_entries.append(response)
		if failed_entry_count>0:return DeleteEventsResponse(status=400,FailedEntryCount=failed_entry_count,FailedEntries=failed_entries)
		return DeleteEventsResponse(status=200,FailedEntryCount=0,FailedEntries=[])
	@route(config.get_relative_url(config.ALL_EVENTS),methods=[_C])
	def delete_all_events(self,request:Request)->DeleteAllEventsResponse:
		response=self.event_service.delete_all_events()
		if response and _A in response:return DeleteAllEventsResponse(status=400,error=response.get(_A))
		return DeleteAllEventsResponse(status=200)
	@route(config.get_relative_url(config.EVENTS),methods=[_B])
	def list_events(self,request:Request)->ListEventsResponse:events=self.event_service.list_events();return ListEventsResponse(status=200,events=events)
	@route(f"{config.get_relative_url(config.EVENTS)}/<span_id>",methods=[_B])
	def get_event(self,request:Request,span_id:str)->GetEventResponse:
		event=self.event_service.get_event(span_id)
		if not event:return GetEventResponse(status=404,error=f"Event with span_id {span_id} not found.")
		return GetEventResponse(status=200,event=event.model_dump())
	@route(f"{config.get_relative_url(config.TRACES)}/<trace_id>",methods=[_B])
	def get_trace_graph(self,request:Request,trace_id:str)->TraceGraphResponse:
		event_graph=self.event_service.get_trace_graph(trace_id=trace_id)
		if event_graph is None:return TraceGraphResponse(status=404,error=f"Trace with id {trace_id} not found.")
		return TraceGraphResponse(status=200,event=event_graph)
	@route(config.get_relative_url(config.REPLAY),methods=['POST'])
	def replay_events(self,request:Request)->ReplayEventsResponse:
		replay_event_list:EventModelList=parse_request_body(request,EventModelList);failed_entry_count=0;failed_entries=[]
		for event_to_replay in replay_event_list.events:
			if not event_to_replay.is_replayable:failed_entry_count+=1;failed_entries.append(event_to_replay);LOG.warning(f"Event {event_to_replay.span_id} is not replayable.");continue
			try:
				event_in_storage=self.event_service.get_event(span_id=event_to_replay.span_id)
				if not event_in_storage:LOG.warning(f"Event {event_to_replay.span_id} not found for replay.");failed_entry_count+=1;failed_entries.append(event_to_replay);continue
				combined_event_data={**event_in_storage.model_dump(),**{k:v for(k,v)in event_to_replay.model_dump().items()if v is not None},'parent_id':event_to_replay.span_id,'operation_name':'ReplayEvent','version':event_in_storage.version+1,'is_replayable':False};replay_input_event=InputEventModel(**combined_event_data);new_span_id,_=self.event_service.store_event(replay_input_event);updated_combined_event_data={**combined_event_data,'span_id':new_span_id};combined_event_for_sending=EventModel(**updated_combined_event_data);trace_context=TraceContext(trace_id=combined_event_for_sending.trace_id,parent_id=combined_event_for_sending.span_id,version=combined_event_for_sending.version);sender=self._get_replay_event_sender(service=combined_event_for_sending.service,account_id=combined_event_for_sending.account_id,region=combined_event_for_sending.region);replay_response=sender.replay_event(event=combined_event_for_sending,trace_context=trace_context)
				if not replay_response or replay_response.get('ResponseMetadata',{}).get('HTTPStatusCode')!=200:LOG.warning(f"Replay failed for event {new_span_id}. Response: {replay_response}");failed_entry_count+=1;failed_entries.append(combined_event_for_sending);self.error_service.store_error(InputErrorModel(span_id=new_span_id,error_message=f"Replay HTTPStatusCode not 200. Got: {replay_response}",error_type=ErrorType.REPLAY_ERROR))
			except(botocore.exceptions.ParamValidationError,botocore.exceptions.ClientError)as e:LOG.error(f"Boto error during replay for {event_to_replay.span_id}: {e}",exc_info=True);failed_entry_count+=1;failed_entries.append(event_to_replay);error_span_id_ref=new_span_id if'new_span_id'in locals()and new_span_id else event_to_replay.span_id;self.error_service.store_error(InputErrorModel(span_id=error_span_id_ref,error_message=str(e),error_type=ErrorType.BOTO_ERROR))
			except Exception as e:LOG.error(f"Unexpected error during replay for {event_to_replay.span_id}: {e}",exc_info=True);failed_entry_count+=1;failed_entries.append(event_to_replay)
		if failed_entry_count>0:return ReplayEventsResponse(status=400,FailedEntryCount=failed_entry_count,FailedEntries=failed_entries)
		return ReplayEventsResponse(status=200,FailedEntryCount=0,FailedEntries=[])
	@route(config.get_relative_url(config.DB_ERRORS),methods=[_B])
	def list_db_errors(self,request:Request)->ListErrorsResponse:errors=self.error_service.list_all_errors();return ListErrorsResponse(status=200,errors=errors)
	@route(config.get_relative_url(config.ALL_ERRORS),methods=[_C])
	def delete_all_errors(self,request:Request)->DeleteAllErrorsResponse:
		response=self.error_service.delete_all_errors()
		if response and _A in response:return DeleteAllErrorsResponse(status=400,error=response.get(_A))
		return DeleteAllErrorsResponse(status=200)
	@route(config.get_relative_url(config.DB_EVENTS),methods=[_B])
	def list_db_events(self,request:Request)->ListEventsResponse:events=self.event_service.list_all_events();return ListEventsResponse(status=200,events=events)