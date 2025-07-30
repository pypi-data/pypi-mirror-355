from eventstudio.types.error import ADDITIONAL_ERROR_MAPPINGS,ERROR_NAME_LOOKUP,ErrorType
def get_error_type(error_name):
	B=error_name
	if B in ERROR_NAME_LOOKUP:return ERROR_NAME_LOOKUP[B]
	C=B.split()[0]
	if C in ADDITIONAL_ERROR_MAPPINGS:return ADDITIONAL_ERROR_MAPPINGS[C]
	A=B.lower()
	if'boto'in A:return ErrorType.BOTO_ERROR
	elif'eventstudio'in A:return ErrorType.EVENTSTUDIO_ERROR
	elif'localstack'in A:return ErrorType.LOCALSTACK_ERROR
	elif'iam'in A:return ErrorType.IAM_ERROR
	elif'param'in A or'validation'in A:return ErrorType.PARAMETER_ERROR
	return ErrorType.LOCALSTACK_ERROR