from pydantic import BaseModel
class DeleteEventsRequest(BaseModel):span_ids:list[str]