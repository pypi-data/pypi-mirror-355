_D='utf-8'
_C=False
_B=True
_A=None
import base64,json,logging,re,xml.etree.ElementTree as ET
from datetime import datetime
from enum import Enum
from json import JSONDecodeError
from typing import Any,Dict,List,Pattern,Tuple,Type,TypeVar,Union
from botocore.client import BaseClient
from localstack.aws.api.events import PutEventsRequestEntry
from localstack.http import Request
from localstack.utils.aws.arns import parse_arn
from pydantic import BaseModel
from sqlalchemy.types import JSON,TypeDecorator
from eventstudio.types.error import ErrorModel,ErrorModelList,ErrorType
from eventstudio.types.event import APIGatewayBodyType,EventModel,EventModelList,EventsEventPartialData,SQSMessageBodyType
from eventstudio.types.services import SERVICE_NAME_LOOKUP,ServiceName
LOG=logging.getLogger(__name__)
LAMBDA_PATTERN=re.compile('^(lambda-func-[0-9a-f]{8})-')
class CustomJSONEncoder(json.JSONEncoder):
	def default(B,obj):
		A=obj
		if isinstance(A,datetime):return A.isoformat()
		if isinstance(A,Enum):return A.value
		if isinstance(A,EventModel):return A.model_dump()
		if isinstance(A,EventModelList):return A.model_dump()
		if isinstance(A,ErrorModel):return A.model_dump()
		if isinstance(A,ErrorModelList):return A.model_dump()
		return super().default(A)
class JSONEncodedDict(TypeDecorator):
	impl=JSON;cache_ok=_B
	def __init__(A,encoder=_A,*B,**C):A.encoder=encoder or CustomJSONEncoder;super().__init__(*B,**C)
	def process_bind_param(B,value,dialect):
		A=value
		if A is not _A:A=json.dumps(A,cls=B.encoder)
		return A
	def process_result_value(B,value,dialect):
		A=value
		if A is not _A:A=json.loads(A)
		return A
def pars_timestamp_ms(timestamp_ms:str)->datetime:A=int(timestamp_ms)/1000;B=datetime.fromtimestamp(A);return B
def convert_raw_entry(entry:PutEventsRequestEntry)->EventsEventPartialData:
	A=entry;B=A.get('Detail','{}')
	try:C=json.loads(B)
	except(TypeError,JSONDecodeError):C=B
	return EventsEventPartialData(version='0',detail_type=A.get('DetailType'),source=A.get('Source'),resources=A.get('Resources',[]),detail=C)
T=TypeVar('T',bound=BaseModel)
def parse_request_body(request:Request,model:Type[T])->T:A=request.data.decode(_D);B=json.loads(A);return model(**B)
def compile_regex_patterns(patterns:List[str])->List[Pattern]:return[re.compile(A)for A in patterns]
def load_sqs_message_body(body:str)->Tuple[Union[Dict[Any,Any],str],SQSMessageBodyType]:
	A=body
	try:return json.loads(A),'JSON'
	except json.JSONDecodeError:pass
	try:
		if A.strip().startswith(('<?xml','<')):B=ET.fromstring(A);return xml_to_dict(B),'XML'
	except ET.ParseError:pass
	return A,'TEXT'
def xml_to_dict(element:ET.Element)->Dict[str,Any]:
	B=element;A={}
	if B.attrib:A.update(B.attrib)
	for C in B:
		D=xml_to_dict(C)
		if C.tag in A:
			if not isinstance(A[C.tag],list):A[C.tag]=[A[C.tag]]
			A[C.tag].append(D)
		else:A[C.tag]=D
	if B.text and B.text.strip():
		if A:A['text']=B.text.strip()
		else:A=B.text.strip()
	return A
def dict_to_xml(data:Union[Dict[str,Any],str],root_name:str='root')->str:
	D=root_name;B=data
	def C(parent:ET.Element,data:Union[Dict[str,Any],str,list])->_A:
		B=parent;A=data
		if isinstance(A,dict):
			G=A.pop('text',_A);H={B:A for(B,A)in A.items()if not isinstance(A,(dict,list))}
			for J in H:A.pop(J)
			B.attrib.update({A:str(B)for(A,B)in H.items()})
			for(I,D)in A.items():
				if isinstance(D,list):
					for E in D:F=ET.SubElement(B,I);C(F,E)
				else:F=ET.SubElement(B,I);C(F,D)
			if G is not _A:B.text=str(G)
		elif isinstance(A,list):
			for E in A:C(B,E)
		else:B.text=str(A)
	if isinstance(B,dict):A=ET.Element(D);C(A,B)
	else:A=ET.Element(D);A.text=str(B)
	return'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(A,encoding='unicode',method='xml')
def log_event_studio_error(logger,service:ServiceName,operation:str,error:str):A={'service':service.value,'operation':operation,'error':str(error)};logger.error(json.dumps({'ErrorCode':ErrorType.EVENTSTUDIO_ERROR.value,'ErrorMessage':A}))
def run_safe(logger,service:ServiceName,operation:str):
	def A(func):
		def A(*A,**B):
			try:return func(*A,**B)
			except Exception as C:log_event_studio_error(logger,service,operation,str(C))
		return A
	return A
def load_apigateway_body(body:bytes|_A)->Tuple[Union[Dict[Any,Any],str,bytes],APIGatewayBodyType]:
	A=body
	if A is _A:return A,'EMPTY'
	try:
		B=A.decode(_D)
		try:return json.loads(B),'JSON'
		except json.JSONDecodeError:pass
		try:
			if B.strip().startswith(('<?xml','<')):C=ET.fromstring(B);return xml_to_dict(C),'XML'
		except ET.ParseError:pass
		return B,'TEXT'
	except UnicodeDecodeError:return A,'BINARY'
def identify_and_decode_sqs_payload(encoded_str):
	C='decoded_json';B='is_json';A='is_base64'
	try:D=base64.b64decode(encoded_str);E=D.decode(_D);F=json.loads(E);return{A:_B,B:_B,C:F}
	except(ValueError,json.JSONDecodeError):return{A:_C,B:_C,C:_A}
def is_lambda_helper_queue(queue_arn:str,lambda_client:BaseClient)->bool:
	A=_C;C=parse_arn(queue_arn);B=C['resource']
	if is_lambda_function(B):
		D=LAMBDA_PATTERN.match(B);E=D.group(1)
		if lambda_exists(E,lambda_client):A=_B
	return A
def is_lambda_function(function_name):return bool(LAMBDA_PATTERN.match(function_name))
def lambda_exists(function_name:str,lambda_client:BaseClient)->bool:
	A=lambda_client
	try:B=A.get_function(FunctionName=function_name);assert B['ResponseMetadata']['HTTPStatusCode']==200;return _B
	except A.exceptions.ResourceNotFoundException:return _C
def get_service_name(value:str)->ServiceName:
	A=value;B=SERVICE_NAME_LOOKUP.get(A)
	if B is _A:raise ValueError(f"No ServiceName enum found for value: {A}")
	return B
def is_internal_call(context):
	A=context
	if A.get(is_internal_call):return A.is_internal_call
	B=next((A[1]for A in A.request.headers if A[0]=='X-Amz-Source-Arn'),_A)
	if B:return _B
	return _C