from localstack.utils.aws.arns import parse_arn
def get_queue_url_from_arn(queue_arn:str)->str:
	A=parse_arn(queue_arn);B=A['account'];C=A['region'];D=A['resource']
	if not all([B,C,D]):raise ValueError('Invalid SQS ARN provided')
	return f"https://sqs.{C}.amazonaws.com/{B}/{D}"