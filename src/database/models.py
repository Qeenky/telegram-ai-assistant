from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}, created_at={self.created_at})>')>"

