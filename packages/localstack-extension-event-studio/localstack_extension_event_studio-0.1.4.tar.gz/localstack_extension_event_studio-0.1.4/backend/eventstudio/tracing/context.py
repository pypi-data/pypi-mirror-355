import json,threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Callable
from localstack.aws.api import RequestContext
from eventstudio.constants import INTERNAL_REQUEST_TRACE_HEADER
from eventstudio.types.trace_context import TraceContext
thread_local_tracing=threading.local()
def get_trace_context()->TraceContext:
	try:return getattr(thread_local_tracing,'trace_context',None)or TraceContext()
	except AttributeError:return TraceContext()
def set_trace_context(trace_context:TraceContext):thread_local_tracing.trace_context=trace_context
def extract_trace_context_from_context(context:RequestContext)->TraceContext:
	A=TraceContext()
	for B in context.request.headers:
		if B[0]==INTERNAL_REQUEST_TRACE_HEADER:A=TraceContext(**json.loads(B[1]));break
	return A
def wrap_function_with_context(fn:Callable,trace_context:TraceContext)->Callable:
	@wraps(fn)
	def A(*A,**B):set_trace_context(trace_context);return fn(*A,**B)
	return A
def submit_with_trace_context(A:ThreadPoolExecutor,B:Callable,*C,**D):E=get_trace_context();F=wrap_function_with_context(B,E);return A.submit(F,*C,**D)
def _get_request_context_stack():
	if not hasattr(thread_local_tracing,'request_context_stack'):thread_local_tracing.request_context_stack=[]
	return thread_local_tracing.request_context_stack
def push_request_context(context:RequestContext):A=_get_request_context_stack();A.append(context)
def pop_request_context()->RequestContext:A=_get_request_context_stack();return A.pop()
def get_request_context()->RequestContext|None:A=_get_request_context_stack();return A[-1]if A else None