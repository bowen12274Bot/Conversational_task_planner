"""
SQLAlchemy models for conversation persistence.

Tables
------
conversations        – one conversation session
conversation_turns   – one user↔AI exchange within a conversation
turn_messages        – individual messages inside a turn
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Conversation(Base):
    """Stores a single conversation session."""

    __tablename__ = "conversations"

    conversation_pk: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_history_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship: one conversation → many turns
    turns: Mapped[list["ConversationTurn"]] = relationship(
        "ConversationTurn",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.created_at",
    )


class ConversationTurn(Base):
    """Stores a single user↔AI exchange round within a conversation."""

    __tablename__ = "conversation_turns"

    turn_pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_pk: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.conversation_pk", ondelete="CASCADE"),
        nullable=False,
    )
    turn_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship: back to parent conversation
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="turns"
    )

    # Relationship: one turn → many messages
    messages: Mapped[list["TurnMessage"]] = relationship(
        "TurnMessage",
        back_populates="turn",
        cascade="all, delete-orphan",
        order_by="TurnMessage.message_index",
    )


class TurnMessage(Base):
    """Stores a single message (user / ai / system) within a turn."""

    __tablename__ = "turn_messages"
    __table_args__ = (
        UniqueConstraint("turn_pk", "message_index", name="uq_turn_message_index"),
    )

    message_pk: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    turn_pk: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversation_turns.turn_pk", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    type: Mapped[str] = mapped_column(Text, nullable=False)  # "user" | "ai" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship: back to parent turn
    turn: Mapped["ConversationTurn"] = relationship(
        "ConversationTurn", back_populates="messages"
    )
