from typing import Optional, List
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Sequence, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        {'schema': 'public'},
    )

    id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    daily_token_limit = Column(Integer, default=10000)
    tokens_used_today = Column(Integer, default=0)

    dialogue = relationship(
        "Dialogue",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}', created_at={self.created_at})>"


class Dialogue(Base):
    __tablename__ = 'dialogues'
    __table_args__ = (
        {'schema': 'public'},
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey('public.users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    conversation_history = Column(JSON, nullable=False, default=list)
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now()
    )

    user = relationship("User", back_populates="dialogue")

    def __init__(self, user_id: int, conversation_history: Optional[List] = None):
        self.user_id = user_id
        self.conversation_history = conversation_history or []

    def __repr__(self):
        return f"<Dialogue(id={self.id}, user_id={self.user_id}, conversation_history={self.conversation_history}, updated_at={self.updated_at})>"


class Subscription(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey('public.users.id', ondelete='CASCADE'),
        nullable=False
    )
    type = Column(String(50))
    status = Column(String(50), default="active")  # "active", "expired", "canceled"
    starts_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, type='{self.type}', status='{self.status}')>"