_A='aws_trace_header'
import logging
from localstack.aws.api import RequestContext
from localstack.utils.xray.trace_header import TraceHeader
from eventstudio.services.trace_link_service import TraceLinkService
from eventstudio.tracing.context import TraceContext,get_trace_context
from eventstudio.utils.utils import compile_regex_patterns
LOG=logging.getLogger(__name__)
XRAY_TRACE_HEADER_PATTERNS=compile_regex_patterns(['Root=([^;]+)'])
XRAY_TRACE_HEADER='X-Amzn-Trace-Id'
def get_trace_context_from_xray_trace_header(xray_trace_header:TraceHeader,trace_link_service:TraceLinkService)->TraceContext:
	try:
		B=xray_trace_header.get(_A)
		if B and(C:=B.root):
			A=trace_link_service.get_trace_context_from_trace_link(C)
			if A.parent_id:return A
	except(IndexError,AttributeError,TypeError):A=get_trace_context();return A
	return TraceContext()
def get_trace_context_from_request_context(context:RequestContext,trace_link_service:TraceLinkService)->TraceContext:
	A=next((A[1]for A in context.request.headers if A[0]==XRAY_TRACE_HEADER),None)
	if not A:return TraceContext()
	try:
		if(C:=extract_xray_trace_id_from_xray_trace_header_str(A)):
			B=trace_link_service.get_trace_context_from_trace_link(C)
			if B.parent_id:return B
	except(IndexError,AttributeError,TypeError):pass
	return TraceContext()
def extract_xray_trace_id_from_xray_trace_header_str(xray_header:str)->str|None:
	try:
		if(B:=XRAY_TRACE_HEADER_PATTERNS[0].search(xray_header)):C=B.group(1);return C
		else:LOG.debug('No X-Ray trace ID found in X-Ray trace header');return
	except KeyError as A:LOG.warning(f"Missing required field in X-Ray trace header: {A}");return
	except Exception as A:LOG.warning(f"Error extracting X-Ray trace ID: {A}");return
def extract_aws_trace_header(trace_context:dict)->TraceHeader|None:
	try:
		B=trace_context.get(_A)
		if not B:LOG.debug('No AWS trace header found in trace context');return
		return B
	except KeyError as A:LOG.warning(f"Missing required field in AWS trace header: {A}");return
	except Exception as A:LOG.warning(f"Error extracting AWS trace header: {A}");return