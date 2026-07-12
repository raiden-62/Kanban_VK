from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import selectinload

from app.models import Card, CardPriority, Column, card_labels


@dataclass(frozen=True)
class CardFilters:
    column_id: int | None = None
    assignee_id: int | None = None
    priority: CardPriority | None = None
    label_id: int | None = None
    q: str | None = None
    overdue: bool = False


def build_card_query(board_id: int, filters: CardFilters) -> Select[tuple[Card]]:
    query = select(Card).options(selectinload(Card.labels)).where(Card.board_id == board_id)

    if filters.column_id is not None:
        query = query.where(Card.column_id == filters.column_id)
    if filters.assignee_id is not None:
        query = query.where(Card.assignee_id == filters.assignee_id)
    if filters.priority is not None:
        query = query.where(Card.priority == filters.priority)
    if filters.label_id is not None:
        query = query.join(card_labels, Card.id == card_labels.c.card_id).where(
            card_labels.c.label_id == filters.label_id
        )
    if filters.q:
        search = f"%{filters.q.strip()}%"
        query = query.where(or_(Card.title.ilike(search), Card.description.ilike(search)))
    if filters.overdue:
        query = query.join(Column, Card.column_id == Column.id).where(
            Card.deadline.is_not(None),
            Card.deadline < date.today(),
            Column.is_done.is_(False),
        )

    return query.distinct().order_by(Card.column_id, Card.position, Card.id)

