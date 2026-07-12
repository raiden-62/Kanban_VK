from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CardPriority
from app.models.label import card_labels


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[CardPriority] = mapped_column(
        Enum(CardPriority, values_callable=lambda obj: [priority.value for priority in obj]),
        nullable=False,
        default=CardPriority.medium,
        server_default=CardPriority.medium.value,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    board = relationship("Board", back_populates="cards")
    column = relationship("Column", back_populates="cards")
    assignee = relationship("User", back_populates="assigned_cards", foreign_keys=[assignee_id])
    comments = relationship("Comment", back_populates="card", cascade="all, delete-orphan")
    labels = relationship("Label", secondary=card_labels, back_populates="cards")
