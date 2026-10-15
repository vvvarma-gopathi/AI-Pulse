from core.database import Base
from sqlalchemy import String,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import func,DateTime
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID


class Users(Base):
    __tablename__="users"

    id:Mapped[UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid4)
    user_name:Mapped[str]=mapped_column(String(225),nullable=False,unique=True)
    name:Mapped[str]=mapped_column(String(225),nullable=False)
    email:Mapped[str]=mapped_column(String(500),nullable=False,unique=True)
    password:Mapped[str]=mapped_column(String(150),nullable=False,unique=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())