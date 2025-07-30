_C='FailedEntries'
_B='FailedEntryCount'
_A=None
from typing import Any
from localstack.aws.api.events import Integer,PutEventsResultEntryList
from pydantic import BaseModel
from rolo import Response
from eventstudio.types.error import ErrorModelList
from eventstudio.types.event import EventModel,EventModelList
from eventstudio.utils.utils import CustomJSONEncoder
class Error(BaseModel):error:str;span_id:str|_A=_A
class FailedEntry(EventModel):error:str
class FailedEntryList(BaseModel):entries:list[FailedEntry]
class BaseEventsResponse(Response):
	def __init__(B,status:int,response_data:dict[str,Any]|_A=_A,error:str|_A=_A):
		D=error;C=response_data;super().__init__();B.status_code=status;A={}
		if D:A['error']=D
		if C:A.update(C)
		if A:B.set_json(A,cls=CustomJSONEncoder)
class AddEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,FailedEntryCount:Integer|_A=_A,FailedEntries:FailedEntryList|_A=_A,error:str|_A=_A):super().__init__(status,{_B:FailedEntryCount,_C:FailedEntries},error)
class DeleteAllEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,error:str|_A=_A):super().__init__(status,error=error)
class DeleteEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,FailedEntryCount:Integer|_A=_A,FailedEntries:FailedEntryList|_A=_A,error:str|_A=_A):super().__init__(status,{_B:FailedEntryCount,_C:FailedEntries},error)
class GetEventResponse(BaseEventsResponse):
	def __init__(A,status:int,event:EventModel|_A=_A,error:str|_A=_A):super().__init__(status,{'event':event},error)
class ListEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,events:EventModelList|_A=_A,error:str|_A=_A):super().__init__(status,{'events':events},error)
class ReplayEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,FailedEntryCount:Integer|_A=_A,FailedEntries:PutEventsResultEntryList|_A=_A,error:str|_A=_A):super().__init__(status,{_B:FailedEntryCount,_C:FailedEntries},error)
class TraceGraphResponse(BaseEventsResponse):
	def __init__(C,status:int,event:EventModel|_A=_A,error:str|_A=_A):A=event;B={A.trace_id:A}if A else{};super().__init__(status,{'traces':B},error)
class UpdateEventsResponse(BaseEventsResponse):
	def __init__(A,status:int,FailedEntryCount:Integer|_A=_A,FailedEntries:FailedEntryList|_A=_A,error:str|_A=_A):super().__init__(status,{_B:FailedEntryCount,_C:FailedEntries},error)
class ListErrorsResponse(BaseEventsResponse):
	def __init__(A,status:int,errors:ErrorModelList|_A=_A,error:str|_A=_A):super().__init__(status,{'errors':errors},error)
class DeleteAllErrorsResponse(BaseEventsResponse):
	def __init__(A,status:int,error:str|_A=_A):super().__init__(status,error=error)