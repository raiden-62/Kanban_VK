from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Board, Card, Column, Label, User
from scripts.seed_mock_data import FEATURE_BOARD, HIRING_BOARD, DEMO_USERS, seed_mock_data


def scalar_count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_seed_mock_data_creates_two_idempotent_demo_boards(db_session: Session) -> None:
    first_created_count = seed_mock_data(db_session)
    db_session.commit()

    assert first_created_count == 2
    assert scalar_count(db_session, Board) == 2
    assert scalar_count(db_session, Column) == len(FEATURE_BOARD.columns) + len(HIRING_BOARD.columns)
    assert scalar_count(db_session, Label) == len(FEATURE_BOARD.labels) + len(HIRING_BOARD.labels)
    assert scalar_count(db_session, Card) == len(FEATURE_BOARD.cards) + len(HIRING_BOARD.cards)
    assert scalar_count(db_session, User) == len(DEMO_USERS)

    second_created_count = seed_mock_data(db_session)
    db_session.commit()

    assert second_created_count == 0
    assert scalar_count(db_session, Board) == 2
    assert scalar_count(db_session, Column) == len(FEATURE_BOARD.columns) + len(HIRING_BOARD.columns)
    assert scalar_count(db_session, Label) == len(FEATURE_BOARD.labels) + len(HIRING_BOARD.labels)
    assert scalar_count(db_session, Card) == len(FEATURE_BOARD.cards) + len(HIRING_BOARD.cards)
    assert scalar_count(db_session, User) == len(DEMO_USERS)


def test_seed_mock_data_assigns_deadlines_and_assignees(db_session: Session) -> None:
    seed_mock_data(db_session)
    db_session.commit()

    cards = db_session.scalars(select(Card)).all()

    assert len(cards) == len(FEATURE_BOARD.cards) + len(HIRING_BOARD.cards)
    assert all(card.deadline is not None for card in cards)
    assert all(card.assignee_id is not None for card in cards)
    assert all(card.labels for card in cards)
