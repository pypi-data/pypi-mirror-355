import logging
from eventstudio.storage.trace_link_repository import TraceLinkRepository
from eventstudio.types.trace_context import TraceContext
from eventstudio.types.trace_link import InputTraceLinkModel
LOG=logging.getLogger(__name__)
class TraceLinkService:
	def __init__(A,trace_link_repository:TraceLinkRepository):(A._trace_link_repository):TraceLinkRepository=trace_link_repository
	def store_trace_link(C,trace_link:str,trace_context:TraceContext):A=trace_context;D=InputTraceLinkModel(trace_link=trace_link,parent_id=A.parent_id,trace_id=A.trace_id,version=A.version);B=C._trace_link_repository.add_trace_link(D);return B.trace_link_id,B.trace_id
	def get_trace_context_from_trace_link(B,trace_link:str)->TraceContext|None:
		A=trace_link;A=B._trace_link_repository.get_trace_link(A)
		if not A:LOG.debug(f"No trace link found for Request ID: {A}");return
		return TraceContext(trace_id=A.trace_id,parent_id=A.parent_id,version=A.version)