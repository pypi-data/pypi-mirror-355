_A=None
import logging
from localstack.services.apigateway.next_gen.execute_api.context import RestApiInvocationContext
from localstack.services.apigateway.next_gen.execute_api.integrations.aws import RestApiAwsProxyIntegration
from localstack.utils.aws.arns import apigateway_restapi_arn
from localstack.utils.patch import Patch
from localstack.utils.xray.trace_header import TraceHeader
from eventstudio.tracing.aws.base import Instrumentation
from eventstudio.tracing.context import TraceContext,set_trace_context
from eventstudio.tracing.xray_tracing import get_trace_context_from_request_context
from eventstudio.types.event import InputEventModel
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import is_internal_call,load_apigateway_body,log_event_studio_error
LOG=logging.getLogger(__name__)
class ApigatewayInstrumentation(Instrumentation):
	def apply(A):Patch.function(RestApiAwsProxyIntegration.invoke,A._invoke_apigateway).apply()
	def _invoke_apigateway(C,fn,self_,context:RestApiInvocationContext,**a)->_A:
		Z='Request';Y='requestId';X='Invoke';W='<binary data>';V='BINARY';U='body';T='headers';P=self_;A=context
		try:
			G=get_trace_context_from_request_context(A,C.trace_link_service);H=G.parent_id;B=G.trace_id;D=G.version;I=A.invocation_request.copy();E=A.deployment.rest_api.rest_api.get('name');J=A.account_id;K=A.region;b=apigateway_restapi_arn(E,J,K);I.pop(T,_A);L,c=load_apigateway_body(I.pop(U,_A))
			if c==V:F=L;L=W
			else:F=_A
			M=A.integration_request.copy();M.pop(T,_A);N,Q=load_apigateway_body(M.pop(U,_A))
			if Q==V:F=N;N=W
			else:F=_A
			if not H and not B:
				D=0
				if is_internal_call(A):d=ServiceName.INTERNAL;R={'service':d,'operation_name':X}
				else:e=ServiceName.EXTERNAL;R={'user_agent':A.request.user_agent.string,'browser':A.request.user_agent.browser,'language':A.request.user_agent.language,'platform':A.request.user_agent.platform,'version':A.request.user_agent.version}
				O=InputEventModel(parent_id=_A,trace_id=_A,event_id=A.context_variables.get(Y),version=D,account_id=J,region=K,service=e,resource_name=E,arn='not_applicable',operation_name=Z,event_metadata=R);H,B=C.event_service.store_event(InputEventModel.model_validate(O))
			O=InputEventModel(parent_id=H,trace_id=B,event_id=A.context_variables.get(Y),version=D,account_id=J,region=K,service=ServiceName.APIGATEWAY,resource_name=E,arn=b,operation_name=Z,is_replayable=True,event_data={'invocation_request_body':L,'integration_request_body':N,'invocation_request':I,'integration_request':M},event_bytedata=F,event_metadata={'api_type':P.name,'api_name':E,'deployment_id':A.deployment_id,'stage_name':A.stage,'body_type':Q});f,B=C.event_service.store_event(InputEventModel.model_validate(O));S=TraceContext(trace_id=B,parent_id=f,version=D);set_trace_context(S)
			if(g:=A.trace_id):h=TraceHeader.from_header_str(g).ensure_root_exists();C.trace_link_service.store_trace_link(trace_link=h.root,trace_context=S)
		except Exception as i:log_event_studio_error(logger=LOG,service=ServiceName.APIGATEWAY,operation=X,error=str(i))
		return fn(P,context=A,**a)