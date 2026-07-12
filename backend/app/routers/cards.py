from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Card, CardPriority, User
from app.schemas.card import CardCreate, CardMove, CardRead, CardUpdate
from app.services.card_filters import CardFilters, build_card_query
from app.services.labels import get_labels_for_board
from app.services.ordering import insert_card, move_card, normalize_card_positions
from app.services.permissions import (
    ensure_user_is_board_member,
    get_card_for_board_or_404,
    get_column_for_board_or_404,
    require_editor,
    require_viewer,
)


router = APIRouter(prefix="/tables/{board_id}/cards", tags=["cards"])


@router.get("", response_model=list[CardRead])
def list_cards(
    board_id: int,
    column_id: int | None = None,
    assignee_id: int | None = None,
    priority: CardPriority | None = None,
    label_id: int | None = None,
    q: str | None = None,
    overdue: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Card]:
    require_viewer(db, board_id, current_user)
    if column_id is not None:
        get_column_for_board_or_404(db, board_id, column_id)
    if label_id is not None:
        get_labels_for_board(db, board_id, [label_id])
    filters = CardFilters(
        column_id=column_id,
        assignee_id=assignee_id,
        priority=priority,
        label_id=label_id,
        q=q,
        overdue=overdue,
    )
    return db.scalars(build_card_query(board_id, filters)).all()


@router.get("/overdue", response_model=list[CardRead])
def list_overdue_cards(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Card]:
    require_viewer(db, board_id, current_user)
    return db.scalars(build_card_query(board_id, CardFilters(overdue=True))).all()


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    board_id: int,
    payload: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Card:
    require_editor(db, board_id, current_user)
    get_column_for_board_or_404(db, board_id, payload.column_id)
    ensure_user_is_board_member(db, board_id, payload.assignee_id)
    labels = get_labels_for_board(db, board_id, payload.label_ids)

    card = Card(
        board_id=board_id,
        column_id=payload.column_id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
        deadline=payload.deadline,
        priority=payload.priority,
        position=0,
    )
    card.labels = labels
    db.add(card)
    insert_card(db, card, payload.position)
    db.commit()
    db.refresh(card)
    return card


@router.get("/{card_id}", response_model=CardRead)
def get_card(
    board_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Card:
    require_viewer(db, board_id, current_user)
    return get_card_for_board_or_404(db, board_id, card_id)


@router.patch("/{card_id}", response_model=CardRead)
def update_card(
    board_id: int,
    card_id: int,
    payload: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Card:
    require_editor(db, board_id, current_user)
    card = get_card_for_board_or_404(db, board_id, card_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "assignee_id" in update_data:
        ensure_user_is_board_member(db, board_id, update_data["assignee_id"])
    if "label_ids" in update_data:
        card.labels = get_labels_for_board(db, board_id, update_data.pop("label_ids"))
    for field, value in update_data.items():
        setattr(card, field, value)
    db.commit()
    db.refresh(card)
    return card


@router.patch("/{card_id}/move", response_model=CardRead)
def move_card_endpoint(
    board_id: int,
    card_id: int,
    payload: CardMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Card:
    require_editor(db, board_id, current_user)
    card = get_card_for_board_or_404(db, board_id, card_id)
    get_column_for_board_or_404(db, board_id, payload.column_id)
    move_card(db, card, payload.column_id, payload.position)
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    board_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_editor(db, board_id, current_user)
    card = get_card_for_board_or_404(db, board_id, card_id)
    column_id = card.column_id
    db.delete(card)
    db.flush()
    normalize_card_positions(db, column_id)
    db.commit()
