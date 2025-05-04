from typing import Annotated
import uuid
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass


intpk = Annotated[int, mapped_column(primary_key=True, index=True, autoincrement=True)]
str100 = Annotated[str, 100]
uuidpk = Annotated[uuid.UUID, mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)]
uuidfk = Annotated[uuid.UUID, mapped_column(UUID(as_uuid=True))]
