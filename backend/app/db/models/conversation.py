"""
SQLAlchemy models for conversation persistence.

Tables
------
conversations        – one conversation session
conversation_turns   – one user↔AI exchange within a conversation
turn_messages        – individual messages inside a turn
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Conversation(Base):
    """Stores a single conversation session (the top-level container)."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        order_by="ConversationTurn.turn_index",
    )


class ConversationTurn(Base):
    """Stores a single user↔AI exchange round within a conversation."""

    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
        order_by="TurnMessage.created_at",
    )


class TurnMessage(Base):
    """Stores a single message (user / ai / system) within a turn."""

    __tablename__ = "turn_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turn_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_turns.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)  # "user" | "ai" | "system"
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
