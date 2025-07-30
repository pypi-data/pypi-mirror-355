_E='errors'
_D='events'
_C='events.span_id'
_B=True
_A=False
import uuid
from datetime import datetime,timezone
from functools import partial
import sqlalchemy as sa
from sqlalchemy import Enum
from sqlalchemy.engine import Engine,create_engine
from sqlalchemy.orm import declarative_base,relationship
from eventstudio.types.error import ErrorType
from eventstudio.types.services import ServiceName
from eventstudio.utils.utils import CustomJSONEncoder,JSONEncodedDict
Base=declarative_base()
class EventDBModel(Base):__tablename__=_D;span_id=sa.Column(sa.String,primary_key=_B,default=lambda:str(uuid.uuid4()));parent_id=sa.Column(sa.String,sa.ForeignKey(_C),nullable=_B);trace_id=sa.Column(sa.String,nullable=_A,default=lambda:str(uuid.uuid4()));event_id=sa.Column(sa.String);is_deleted=sa.Column(sa.Boolean,default=_A,nullable=_A);creation_time=sa.Column(sa.DateTime,nullable=_A,default=partial(datetime.now,tz=timezone.utc));status=sa.Column(sa.String,default='OK',nullable=_A);account_id=sa.Column(sa.String,nullable=_A);region=sa.Column(sa.String,nullable=_A);service=sa.Column(Enum(ServiceName),nullable=_A);resource_name=sa.Column(sa.String,nullable=_A);arn=sa.Column(sa.String,nullable=_A);operation_name=sa.Column(sa.String,nullable=_A);errors=relationship('ErrorDBModel',back_populates=_D);version=sa.Column(sa.Integer,nullable=_A,default=0);is_replayable=sa.Column(sa.Boolean,nullable=_A,default=_A);is_edited=sa.Column(sa.Boolean,nullable=_A,default=_A);is_hidden=sa.Column(sa.Boolean,nullable=_A,default=_A);event_data=sa.Column(JSONEncodedDict(encoder=CustomJSONEncoder),nullable=_A);event_bytedata=sa.Column(sa.BLOB,nullable=_B);event_metadata=sa.Column(JSONEncodedDict(encoder=CustomJSONEncoder))
class ErrorDBModel(Base):__tablename__=_E;error_id=sa.Column(sa.String,primary_key=_B,default=lambda:str(uuid.uuid4()));span_id=sa.Column(sa.String,sa.ForeignKey(_C),nullable=_A);error_message=sa.Column(sa.String,nullable=_A);error_type=sa.Column(Enum(ErrorType),nullable=_A);creation_time=sa.Column(sa.DateTime,nullable=_A,default=partial(datetime.now,tz=timezone.utc));events=relationship('EventDBModel',back_populates=_E)
class TraceLinkDBModel(Base):__tablename__='trace_links';trace_link_id=sa.Column(sa.String,primary_key=_B,default=lambda:str(uuid.uuid4()));creation_time=sa.Column(sa.DateTime,nullable=_A,default=partial(datetime.now,tz=timezone.utc));trace_link=sa.Column(sa.String,nullable=_A);parent_id=sa.Column(sa.String,sa.ForeignKey(_C),nullable=_A);trace_id=sa.Column(sa.String,sa.ForeignKey('events.trace_id'),nullable=_A);version=sa.Column(sa.Integer,nullable=_A)
def get_engine(db_path:str)->Engine:A=create_engine(f"sqlite:///{db_path}",echo=_B);Base.metadata.create_all(A);return A