import logging
from eventstudio.storage.error_repository import ErrorRepository
from eventstudio.types.error import InputErrorModel
LOG=logging.getLogger(__name__)
class ErrorService:
	def __init__(A,error_repository:ErrorRepository):(A._error_repository):ErrorRepository=error_repository
	def store_error(B,error:InputErrorModel)->tuple[str,str]:A=B._error_repository.add_error(error);return A.error_id,A.span_id
	def list_all_errors(A)->list[InputErrorModel]:return A._error_repository.get_all_errors()
	def delete_all_errors(A)->None:A._error_repository.delete_all_errors()