from sqlalchemy import ForeignKey, String, Table, UniqueConstraint, Column as SaColumn
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


card_labels = Table(
    "card_labels",
    Base.metadata,
    SaColumn("card_id", ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    SaColumn("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("board_id", "title", name="uq_board_label_title"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)

    board = relationship("Board", back_populates="labels")
    cards = relationship("Card", secondary=card_labels, back_populates="labels")
