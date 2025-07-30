import logging
from sqlalchemy import desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from eventstudio.db.models import TraceLinkDBModel
from eventstudio.types.trace_link import TraceLinkModel
LOG=logging.getLogger(__name__)
class TraceLinkRepository:
	def __init__(A,engine:Engine):(A._engine):Engine=engine
	def add_trace_link(C,trace_link:TraceLinkModel)->TraceLinkModel:
		with Session(C._engine)as A:B=TraceLinkDBModel(**trace_link.model_dump());A.add(B);A.commit();return TraceLinkModel.model_validate(B)
	def get_trace_link(B,trace_link:str)->TraceLinkModel|None:
		A=trace_link
		with Session(B._engine)as C:
			A=C.query(TraceLinkDBModel).filter(TraceLinkDBModel.trace_link==A).order_by(desc(TraceLinkDBModel.creation_time)).first()
			if not A:return
			return TraceLinkModel.model_validate(A)
	def get_all_trace_links(A)->list[TraceLinkModel]:
		with Session(A._engine)as B:C=B.query(TraceLinkDBModel).all();return[TraceLinkModel.model_validate(A)for A in C]
	def delete_all_trace_links(B):
		with Session(B._engine)as A:A.query(TraceLinkDBModel).delete();A.commit()