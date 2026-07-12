from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, Column


def clamp_position(position: int | None, item_count: int) -> int:
    if position is None:
        return item_count
    return max(0, min(position, item_count))


def normalize_column_positions(db: Session, board_id: int) -> None:
    columns = db.scalars(
        select(Column).where(Column.board_id == board_id).order_by(Column.position, Column.id)
    ).all()
    for index, column in enumerate(columns):
        column.position = index


def insert_column(db: Session, column: Column, position: int | None) -> None:
    with db.no_autoflush:
        columns = db.scalars(
            select(Column)
            .where(Column.board_id == column.board_id, Column.id != column.id)
            .order_by(Column.position, Column.id)
        ).all()
    insert_at = clamp_position(position, len(columns))
    columns.insert(insert_at, column)
    for index, existing_column in enumerate(columns):
        existing_column.position = index


def normalize_card_positions(db: Session, column_id: int) -> None:
    cards = db.scalars(
        select(Card).where(Card.column_id == column_id).order_by(Card.position, Card.id)
    ).all()
    for index, card in enumerate(cards):
        card.position = index


def insert_card(db: Session, card: Card, position: int | None) -> None:
    with db.no_autoflush:
        cards = db.scalars(
            select(Card)
            .where(Card.column_id == card.column_id, Card.id != card.id)
            .order_by(Card.position, Card.id)
        ).all()
    insert_at = clamp_position(position, len(cards))
    cards.insert(insert_at, card)
    for index, existing_card in enumerate(cards):
        existing_card.position = index


def move_card(db: Session, card: Card, target_column_id: int, target_position: int) -> None:
    source_column_id = card.column_id
    if source_column_id == target_column_id:
        cards = db.scalars(
            select(Card)
            .where(Card.column_id == source_column_id, Card.id != card.id)
            .order_by(Card.position, Card.id)
        ).all()
        insert_at = clamp_position(target_position, len(cards))
        cards.insert(insert_at, card)
        for index, existing_card in enumerate(cards):
            existing_card.position = index
        return

    source_cards = db.scalars(
        select(Card)
        .where(Card.column_id == source_column_id, Card.id != card.id)
        .order_by(Card.position, Card.id)
    ).all()
    for index, source_card in enumerate(source_cards):
        source_card.position = index

    target_cards = db.scalars(
        select(Card).where(Card.column_id == target_column_id).order_by(Card.position, Card.id)
    ).all()
    insert_at = clamp_position(target_position, len(target_cards))
    card.column_id = target_column_id
    target_cards.insert(insert_at, card)
    for index, target_card in enumerate(target_cards):
        target_card.position = index
