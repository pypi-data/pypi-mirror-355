_A=None
class AppBaseException(Exception):
	def __init__(A,message:str,original_exception:Exception|_A=_A):B=message;super().__init__(B);A.original_exception=original_exception;A.message=B
class RepositoryError(AppBaseException):0
class DatabaseOperationFailedError(RepositoryError):0
class EventNotFoundError(RepositoryError):
	def __init__(B,identifier:str,message:str|_A=_A,original_exception:Exception|_A=_A):A=identifier;B.identifier=A;super().__init__(message or f"Event with identifier '{A}' not found.",original_exception)