from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    is_directory = Column(Boolean, default=False)
    type = Column(String)
    created_at = Column(String)
    filename = Column(String, index=True)
    size = Column(Integer)
