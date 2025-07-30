from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship

class Click(Base):
    __tablename__ = 'clicks'

    url_id = Column(Integer, ForeignKey('urls.id', ondelete="CASCADE"), nullable=False)
    ip_address = Column(String, nullable = False, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False, primary_key=True)

    url = relationship("Url", back_populates="click_record")

class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key = True, nullable=False)
    original = Column(String, nullable = False)
    short_code = Column(String, nullable = False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable= False, server_default = text('now()'))
    clicks = Column(Integer, nullable = False, server_default = text('0'))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                                          nullable=False)

    owner = relationship("User")
    click_record = relationship("Click", back_populates="url", cascade="all, delete")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, nullable=False)
    full_name = Column(String, nullable = False)
    email = Column(String, nullable = False, unique = True)
    urls_created = Column(Integer, nullable = False, server_default = text('0'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, 
                        server_default= text('now()'))
    password = Column(String, nullable = False)
    
# class TokenBlacklist(Base):
#     __tablename__ = 'token_blacklist'

#     id = Column(Integer, primary_key = True, nullable = False)
#     jti = Column(String, unique = True, nullable = False)
#     expires_at = Column(TIMESTAMP(timezone=True), nullable = False)


