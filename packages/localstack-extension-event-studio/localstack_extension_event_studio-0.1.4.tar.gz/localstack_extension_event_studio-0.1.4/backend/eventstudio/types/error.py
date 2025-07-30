from datetime import datetime,timezone
from enum import Enum
from pydantic import BaseModel,ConfigDict,field_validator
class ErrorType(Enum):BOTO_ERROR='boto_error';LOCALSTACK_ERROR='localstack_error';PARAMETER_ERROR='parameter_error';IAM_ERROR='iam_error';LOCALSTACK_WARNING='localstack_warning';EXECUTION_ERROR='execution_error';EVENTSTUDIO_ERROR='eventstudio_error'
ERRORS=[ErrorType.BOTO_ERROR,ErrorType.LOCALSTACK_ERROR,ErrorType.PARAMETER_ERROR,ErrorType.EXECUTION_ERROR,ErrorType.EVENTSTUDIO_ERROR]
WARNINGS=[ErrorType.LOCALSTACK_WARNING]
IAM_PERMISSION=[ErrorType.IAM_ERROR]
ERROR_NAME_VALUES={A.value for A in ErrorType}
ERROR_NAME_LOOKUP={A.value:A for A in ErrorType}
ADDITIONAL_ERROR_MAPPINGS={'ResourceNotFoundException':ErrorType.LOCALSTACK_ERROR,'MalformedDetail':ErrorType.LOCALSTACK_ERROR,'ClientError':ErrorType.BOTO_ERROR,'ValidationError':ErrorType.PARAMETER_ERROR,'ParamValidationError':ErrorType.PARAMETER_ERROR}
class InputErrorModel(BaseModel):span_id:str;error_type:ErrorType;error_message:str
class ErrorModel(InputErrorModel):
	model_config=ConfigDict(from_attributes=True);error_id:str;creation_time:datetime
	@field_validator('creation_time',mode='after')
	@classmethod
	def ensure_utc(cls,value:datetime)->datetime:
		A=value
		if A.tzinfo is None:return A.replace(tzinfo=timezone.utc)
		return A.astimezone(timezone.utc)
class ErrorModelList(BaseModel):errors:list[ErrorModel]