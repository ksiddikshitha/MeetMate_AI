from datetime import datetime, date, UTC
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
class Meeting(Base):
    __tablename__='meetings'
    id: Mapped[int]=mapped_column(primary_key=True)
    title: Mapped[str]=mapped_column(String(250), index=True)
    meeting_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    participants: Mapped[str|None]=mapped_column(Text, nullable=True)
    transcript: Mapped[str]=mapped_column(Text)
    summary: Mapped[str]=mapped_column(Text)
    discussion_points: Mapped[list]=mapped_column(JSON, default=list)
    demo_mode: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))
    decisions=relationship('Decision', cascade='all, delete-orphan', back_populates='meeting')
    actions=relationship('ActionItem', cascade='all, delete-orphan', back_populates='meeting')
    clarifications=relationship('Clarification', cascade='all, delete-orphan', back_populates='meeting')
class Decision(Base):
    __tablename__='decisions'
    id: Mapped[int]=mapped_column(primary_key=True)
    meeting_id: Mapped[int]=mapped_column(ForeignKey('meetings.id', ondelete='CASCADE'), index=True)
    description: Mapped[str]=mapped_column(Text)
    owner: Mapped[str|None]=mapped_column(String(200), nullable=True)
    evidence: Mapped[str|None]=mapped_column(Text, nullable=True)
    timestamp: Mapped[str|None]=mapped_column(String(80), nullable=True)
    meeting=relationship('Meeting', back_populates='decisions')
class ActionItem(Base):
    __tablename__='action_items'
    id: Mapped[int]=mapped_column(primary_key=True)
    meeting_id: Mapped[int]=mapped_column(ForeignKey('meetings.id', ondelete='CASCADE'), index=True)
    title: Mapped[str]=mapped_column(String(300))
    description: Mapped[str]=mapped_column(Text, default='')
    owner: Mapped[str|None]=mapped_column(String(200), nullable=True)
    deadline: Mapped[date|None]=mapped_column(Date, nullable=True, index=True)
    priority: Mapped[str]=mapped_column(String(20), default='Unknown')
    status: Mapped[str]=mapped_column(String(30), default='Pending', index=True)
    evidence: Mapped[str|None]=mapped_column(Text, nullable=True)
    meeting=relationship('Meeting', back_populates='actions')
    clarifications=relationship('Clarification', cascade='all, delete-orphan', back_populates='action')
class Clarification(Base):
    __tablename__='clarifications'
    id: Mapped[int]=mapped_column(primary_key=True)
    meeting_id: Mapped[int]=mapped_column(ForeignKey('meetings.id', ondelete='CASCADE'), index=True)
    action_item_id: Mapped[int|None]=mapped_column(ForeignKey('action_items.id', ondelete='CASCADE'), nullable=True)
    ambiguity: Mapped[str]=mapped_column(Text)
    question: Mapped[str]=mapped_column(Text)
    field: Mapped[str]=mapped_column(String(100))
    original_statement: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(20), default='Open', index=True)
    response: Mapped[str|None]=mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    action=relationship('ActionItem', back_populates='clarifications')
    meeting=relationship('Meeting', back_populates='clarifications')



