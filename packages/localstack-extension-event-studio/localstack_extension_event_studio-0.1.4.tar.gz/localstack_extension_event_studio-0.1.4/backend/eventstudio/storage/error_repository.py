import logging.config
from typing import List
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from eventstudio.db.models import ErrorDBModel
from eventstudio.types.error import ErrorModel,InputErrorModel
from eventstudio.types.responses import Error
LOG=logging.getLogger(__name__)
class ErrorRepository:
	def __init__(A,engine:Engine):(A._engine):Engine=engine
	def add_error(C,error:InputErrorModel)->ErrorModel:
		with Session(C._engine)as A:B=ErrorDBModel(**error.model_dump());A.add(B);A.commit();return ErrorModel.model_validate(B)
	def get_all_errors(A)->List[ErrorModel]:
		with Session(A._engine)as B:C=B.query(ErrorDBModel).all();return[ErrorModel.model_validate(A)for A in C]
	def delete_all_errors(B)->Error|None:
		with Session(B._engine)as A:A.query(ErrorDBModel).delete();A.commit()