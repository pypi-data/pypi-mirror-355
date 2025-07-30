_B=None
_A='PutObject'
import logging,uuid
from localstack.aws.api import RequestContext
from localstack.aws.api.s3 import PutObjectRequest
from localstack.services.s3.models import S3Bucket,S3Object
from localstack.services.s3.notifications import S3EventNotificationContext
from localstack.services.s3.provider import S3Provider
from localstack.utils.patch import Patch
from eventstudio.context import AppContext
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.context import TraceContext,get_trace_context,set_trace_context,submit_with_trace_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import compile_regex_patterns,log_event_studio_error
LOG=logging.getLogger(__name__)
IGNORE_BUCKET_PATTERNS=compile_regex_patterns(['awslambda-.*-tasks'])
class S3Instrumentation(Instrumentation):
	def __init__(A,app_context:AppContext):super().__init__(app_context);(A._bucket_version_status):dict[str,bool]={}
	def apply(A):Patch.function(S3Provider.put_object,A._put_object_s3_bucket).apply();Patch.function(S3Provider._notify,A._patch_notify).apply()
	def _put_object_s3_bucket(F,fn,self_,context:RequestContext,request:PutObjectRequest,**D)->dict:
		C=self_;B=request;A=context
		try:
			E=B.get('Bucket')
			if any(A.match(E)for A in IGNORE_BUCKET_PATTERNS):return fn(C,context=A,request=B,**D)
			G=A.account_id;H=A.region;F._enable_versioning_on_bucket(E,G,H)
		except Exception as I:log_event_studio_error(logger=LOG,service=ServiceName.S3,operation=_A,error=str(I))
		return fn(C,context=A,request=B,**D)
	def _patch_notify(K,fn,self_,context,s3_bucket:S3Bucket,s3_object:S3Object|_B=_B,**H)->_B:
		G=self_;D=s3_bucket;B=s3_object;A=context
		try:
			C=D.name
			if not B or A.service_operation.operation!=_A or any(A.match(C)for A in IGNORE_BUCKET_PATTERNS):return fn(G,context=A,s3_bucket=D,s3_object=B,**H)
			L=A.account_id;M=A.region;I=B.key;N=B.version_id;E=get_trace_context();O=E.parent_id;F=E.trace_id;J=E.version;P=InputEventModel(parent_id=O,trace_id=F,event_id=uuid.uuid4().hex,version=J,account_id=L,region=M,service=ServiceName.S3,resource_name=C,arn=f"arn:aws:s3:::{C}/{I}",operation_name=_A,is_replayable=True,event_metadata={'bucket':C,'key':I,'data_type':'UNKNOWN','version_id':N});Q,F=K.event_service.store_event(InputEventModel.model_validate(P));R=TraceContext(trace_id=F,parent_id=Q,version=J);set_trace_context(R)
		except Exception as S:log_event_studio_error(logger=LOG,service=ServiceName.S3,operation=_A,error=str(S))
		return fn(G,context=A,s3_bucket=D,s3_object=B,**H)
	def _submit_s3_notification_with_context(A,fn,self_,notifier,ctx:S3EventNotificationContext,config):return submit_with_trace_context(self_._executor,notifier.notify,ctx,config)
	def _enable_versioning_on_bucket(A,bucket_name:str,account_id:str,region:str)->_B:
		B=bucket_name
		if B in A._bucket_version_status and A._bucket_version_status[B]:return
		A.client(account_id,region).s3.put_bucket_versioning(Bucket=B,VersioningConfiguration={'Status':'Enabled'});A._bucket_version_status[B]=True