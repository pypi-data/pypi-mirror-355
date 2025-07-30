from enum import Enum
class ServiceName(Enum):APIGATEWAY='apigateway';DYNAMODB='dynamodb';EVENTS='events';EVENT_STUDIO='event_studio';EXTERNAL='external';INTERNAL='internal';SQS='sqs';LAMBDA='lambda';SNS='sns';S3='s3'
SERVICE_NAME_VALUES={A.value for A in ServiceName}
SERVICE_NAME_LOOKUP={A.value:A for A in ServiceName}