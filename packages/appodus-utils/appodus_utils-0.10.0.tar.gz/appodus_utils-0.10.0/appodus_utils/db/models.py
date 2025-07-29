import uuid
from datetime import datetime
from typing import TypeVar, Optional, Generic, List

from pydantic import BaseModel, Field
from sqlalchemy import Column, Boolean, UUID, TIMESTAMP, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr, DeclarativeBase

from appodus_utils import Utils


class AutoRepr(object):
    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(items))


class Object(BaseModel, AutoRepr):
    pass


# class CustomDateTime(TypeDecorator):
#     impl = DateTime
#
#     def process_bind_param(self, value, dialect):
#         return str_to_datetime(value)


class Base(DeclarativeBase):
    pass


class BaseEntity(Base, AutoRepr):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    # __table_args__ = {
    #     'extend_existing': True,
    #     'postgresql_partition_by': 'RANGE (date_created)'  # Optional for large tables
    # }

    # UUID as PK (PostgreSQL-native)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        index=True
    )

    # Optimized timestamp columns
    date_created = Column(
        TIMESTAMP(timezone=True),
        default=Utils.datetime_now_to_db,
        nullable=False,
        # index=True
    )

    created_by = Column(
        String(36),
        nullable=True
    )

    date_updated = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    updated_by = Column(
        String(36),
        nullable=True
    )

    # Soft delete pattern
    deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True  # Important for filtering active records
    )

    date_deleted = Column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    deleted_by = Column(
        String(36),
        nullable=True
    )

    version = Column(
        Integer,
        default=0,
        nullable=False
    )

    # __mapper_args__ = {
    #     'version_id_col': version,
    #     'version_id_generator': False  # Let PostgreSQL handle increments
    # }

    @hybrid_property
    def is_active(self):
        return ~self.deleted


ModelType = TypeVar("ModelType", bound=BaseEntity)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Object)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Object)
SearchSchemaType = TypeVar("SearchSchemaType", bound=Object)
QuerySchemaType = TypeVar("QuerySchemaType", bound=Object)


class BaseQueryDto(Object):
    id: Optional[str] = Field(None, description='Unique ID')
    date_updated: Optional[datetime] = Field(None, description='Date updated')
    updated_by: Optional[str] = Field(None, description='Who updated the record')
    deleted: Optional[bool] = Field(None, description='Whether deleted')
    date_deleted: Optional[datetime] = Field(None, description='Date deleted')
    deleted_by: Optional[str] = Field(None, description='Who deleted the record')
    date_created: Optional[datetime] = Field(None, description='Date created')
    created_by: Optional[str] = Field(None, description='Who created thee record')
    version: Optional[int] = Field(None, description='The current version number of the record')


T = TypeVar('T', bound=BaseQueryDto)


class Page(Object, Generic[T]):
    data: List[T]
    page: int = 0
    page_size: int = 10
    count: int
    total: int = 0
    prev_page: Optional[int]
    next_page: Optional[int]


# @dataclass  # use instead of Object for pydantic data validation
class PageRequest(Object):
    page: int = 0
    page_size: int = 10
    query_fields: Optional[str] = Field(None, description='Comma separated list of return fields')
    exact_string_values: Optional[bool] = True
    order_by: Optional[str] = Field('date_created desc', description='e.g: username asc, firstname desc')
    where: Optional[str] = Field(None, description='e.g: date_created >=')

# def str_to_datetime(value: str):
#     if type(value) is str:
#         try:
#             return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
#         except ValueError as exc:
#             try:
#                 return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')
#             except ValueError as exc:
#                 try:
#                     return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
#                 except ValueError as exc:
#                     try:
#                         return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
#                     except ValueError as exc:
#                         return datetime.strptime(value, '%Y-%m-%d')
#
#     return value
