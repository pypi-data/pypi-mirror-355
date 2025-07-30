_A=None
from pydantic import BaseModel,ConfigDict
class TraceContext(BaseModel):model_config=ConfigDict(extra='forbid');trace_id:str|_A=_A;parent_id:str|_A=_A;version:int=0