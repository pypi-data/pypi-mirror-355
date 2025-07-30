from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,field_validator
class InputTraceLinkModel(BaseModel):trace_link:str;parent_id:str;trace_id:str;version:int
class TraceLinkModel(InputTraceLinkModel):
	model_config=ConfigDict(from_attributes=True);trace_link_id:str;creation_time:datetime
	@field_validator('creation_time',mode='after')
	@classmethod
	def ensure_utc(cls,value:datetime)->datetime:
		A=value
		if A.tzinfo is None:return A.replace(tzinfo=timezone.utc)
		return A.astimezone(timezone.utc)