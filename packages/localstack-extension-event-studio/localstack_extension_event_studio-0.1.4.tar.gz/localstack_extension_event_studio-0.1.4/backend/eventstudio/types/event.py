_I='RequestResponse'
_H='BINARY'
_G='JSON'
_F='TEXT'
_E=False
_D='data'
_C='metadata'
_B='forbid'
_A=None
from datetime import datetime,timezone
from enum import Enum
from typing import Any,ClassVar,Dict,Literal
from pydantic import BaseModel,ConfigDict,field_validator,model_validator
from eventstudio.types.error import ErrorModel
from eventstudio.types.services import ServiceName
RegionName=str
SQSMessageBodyType=Literal[_F,_G,'XML']
S3DataType=Literal[_F,_H,'UNKNOWN']
APIGatewayBodyType=Literal[_F,_H,_G,'XML','EMPTY']
class APIGatewayEventData(BaseModel):model_config=ConfigDict(extra=_B);invocation_request_body:dict|str;integration_request_body:dict|str;invocation_request:dict;integration_request:dict
class APIGatewayEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);api_type:str;api_name:str;deployment_id:str;stage_name:str;body_type:APIGatewayBodyType
class DynamoDBEventData(BaseModel):model_config=ConfigDict(extra=_B);item:dict[str,str|dict]|_A=_A;records:list[dict[str,str|dict]]|_A=_A
class DynamoDBEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);table_name:str;operation:Literal['PutItem','UpdateItem','DeleteItem','GetItem']|_A=_A;stream_type:Literal['NEW_IMAGE','OLD_IMAGE','NEW_AND_OLD_IMAGES','KEYS_ONLY']|_A=_A
class EventsEventData(BaseModel):model_config=ConfigDict(extra=_B);version:int;detail_type:str;source:str;resources:list[str]|_A;detail:dict|str
class EventsEventPartialData(BaseModel):model_config=ConfigDict(extra=_B);version:int;detail_type:str|_A;source:str|_A;resources:list[str]|_A;detail:dict|str|_A
class EventsEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);event_bus_name:str;replay_name:str|_A=_A;original_time:datetime|_A=_A
class ExternalEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);user_agent:str;browser:str|_A=_A;language:str|_A=_A;platform:str|_A=_A;version:int|_A=_A
class LambdaEventData(BaseModel):model_config=ConfigDict(extra=_B);payload:dict|str|_A=_A;response:dict|str|_A=_A
class InternalEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);service:ServiceName;operation_name:str
class LambdaEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);function_name:str;invocation_type:Literal[_I,'Event','DryRun']=_I;log_type:str|_A=_A;qualifier:str|_A=_A;client_context:str|_A=_A
class SNSEventData(BaseModel):model_config=ConfigDict(extra=_B);message:dict|str
class SNSEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);message_group_id:str|_A=_A;message_structure:Literal[_G]|_A=_A;topic_arn:str
class SQSEventData(BaseModel):model_config=ConfigDict(extra=_B);body:dict|str
class SQSEventMetadata(BaseModel):model_config=ConfigDict(extra=_B);queue_arn:str;body_type:SQSMessageBodyType;message_attributes:dict|_A=_A;message_system_attributes:dict|_A=_A;original_time:datetime|_A=_A;queue_url:str
class S3EventMetadata(BaseModel):model_config=ConfigDict(extra=_B);bucket:str;key:str;data_type:S3DataType;version_id:str
class InputEventModel(BaseModel):
	model_config=ConfigDict(extra='ignore');parent_id:str|_A=_A;trace_id:str|_A=_A;event_id:str|_A=_A;version:int=0;status:str='OK';is_deleted:bool=_E;is_replayable:bool=_E;is_edited:bool=_E;is_hidden:bool=_E;account_id:str;region:str;service:ServiceName;resource_name:str;arn:str;operation_name:str;SERVICE_MAPPINGS:ClassVar[Dict[ServiceName,Dict[str,tuple]]]={ServiceName.APIGATEWAY:{_D:(APIGatewayEventData,),_C:(APIGatewayEventMetadata,)},ServiceName.DYNAMODB:{_D:(DynamoDBEventData,),_C:(DynamoDBEventMetadata,)},ServiceName.EVENTS:{_D:(EventsEventData,EventsEventPartialData),_C:(EventsEventMetadata,)},ServiceName.EXTERNAL:{_C:(ExternalEventMetadata,)},ServiceName.LAMBDA:{_D:(LambdaEventData,),_C:(LambdaEventMetadata,)},ServiceName.INTERNAL:{_C:(InternalEventMetadata,)},ServiceName.SNS:{_D:(SNSEventData,),_C:(SNSEventMetadata,)},ServiceName.SQS:{_D:(SQSEventData,),_C:(SQSEventMetadata,)},ServiceName.S3:{_C:(S3EventMetadata,)}}
	@model_validator(mode='before')
	def convert_event_types(cls,values:Dict[str,Any])->Dict[str,Any]:
		I='event_metadata';H='event_data';C='service';A=values
		if not isinstance(A,dict):A={B:getattr(A,B)for B in dir(A)if not B.startswith('_')and not callable(getattr(A,B))}
		B=A.get(C)
		if isinstance(B,str):
			try:A[C]=ServiceName(B.lower())
			except ValueError:raise ValueError(f"Invalid service name: {B}")
		elif isinstance(B,Enum):A[C]=ServiceName(B.value)
		elif not isinstance(B,ServiceName):return A
		D=A.get(H)
		if isinstance(D,dict):
			E=cls.SERVICE_MAPPINGS[A[C]][_D]
			for J in E:
				try:A[H]=J.model_validate(D);break
				except Exception:pass
			else:raise ValueError(f"Failed to validate event_data with any of these: {', '.join(A.__name__ for A in E)}")
		F=A.get(I)
		if isinstance(F,dict):
			G=cls.SERVICE_MAPPINGS[A[C]][_C]
			for K in G:
				try:A[I]=K.model_validate(F);break
				except Exception:pass
			else:raise ValueError(f"Failed to validate `event_metadata` with any of these: {', '.join(A.__name__ for A in G)}")
		return A
	event_data:APIGatewayEventData|DynamoDBEventData|EventsEventData|EventsEventPartialData|LambdaEventData|SNSEventData|SQSEventData|_A=_A;event_metadata:APIGatewayEventMetadata|DynamoDBEventMetadata|EventsEventMetadata|ExternalEventMetadata|LambdaEventMetadata|InternalEventMetadata|SNSEventMetadata|SQSEventMetadata|S3EventMetadata|_A=_A;event_bytedata:bytes|_A=_A
	@model_validator(mode='after')
	def validate_event_data(cls,values):
		H=' or ';A=values;B=A.service;D=A.event_data;E=A.event_metadata
		if D is not _A:
			F=cls.SERVICE_MAPPINGS[B][_D]
			if not isinstance(D,F):C=H.join(A.__name__ for A in F);raise ValueError(f'For service "{B}", event_data must be of type {C}.')
		if E is not _A:
			G=cls.SERVICE_MAPPINGS[B][_C]
			if not isinstance(E,G):C=H.join(A.__name__ for A in G);raise ValueError(f'For service "{B}", event_metadata must be of type {C}.')
		return A
class InputEventModelList(BaseModel):events:list[InputEventModel]
class EventModel(InputEventModel):
	model_config=ConfigDict(from_attributes=True);span_id:str;creation_time:datetime;errors:list['ErrorModel']=[];children:list['EventModel']=[]
	@field_validator('creation_time',mode='after')
	@classmethod
	def ensure_utc(cls,value:datetime)->datetime:
		A=value
		if A.tzinfo is _A:return A.replace(tzinfo=timezone.utc)
		return A.astimezone(timezone.utc)
class EventModelList(BaseModel):events:list[EventModel]