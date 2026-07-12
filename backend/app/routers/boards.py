from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Board, BoardMember, BoardRole, Card, Column, Label, User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.schemas.kanban import KanbanRead
from app.services.permissions import get_board_or_404, require_owner, require_viewer


router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=list[BoardRead])
def list_boards(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Board]:
    return db.scalars(
        select(Board)
        .join(BoardMember)
        .where(BoardMember.user_id == current_user.id)
        .order_by(Board.updated_at.desc(), Board.id.desc())
    ).all()


@router.post("", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
def create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Board:
    board = Board(title=payload.title, description=payload.description, owner_id=current_user.id)
    db.add(board)
    db.flush()
    db.add(BoardMember(board_id=board.id, user_id=current_user.id, role=BoardRole.owner))
    db.commit()
    db.refresh(board)
    return board


@router.get("/{board_id}/kanban", response_model=KanbanRead)
def get_kanban(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KanbanRead:
    require_viewer(db, board_id, current_user)
    board = get_board_or_404(db, board_id)
    columns = db.scalars(
        select(Column).where(Column.board_id == board_id).order_by(Column.position, Column.id)
    ).all()
    cards = db.scalars(
        select(Card)
        .options(selectinload(Card.labels))
        .where(Card.board_id == board_id)
        .order_by(Card.column_id, Card.position, Card.id)
    ).all()
    labels = db.scalars(select(Label).where(Label.board_id == board_id).order_by(Label.title, Label.id)).all()
    members = db.scalars(
        select(BoardMember)
        .options(joinedload(BoardMember.user))
        .where(BoardMember.board_id == board_id)
        .order_by(BoardMember.id)
    ).all()
    return KanbanRead(board=board, columns=columns, cards=cards, labels=labels, members=members)


@router.get("/{board_id}", response_model=BoardRead)
def get_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Board:
    require_viewer(db, board_id, current_user)
    return get_board_or_404(db, board_id)


@router.patch("/{board_id}", response_model=BoardRead)
def update_board(
    board_id: int,
    payload: BoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Board:
    require_owner(db, board_id, current_user)
    board = get_board_or_404(db, board_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)
    db.commit()
    db.refresh(board)
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_owner(db, board_id, current_user)
    board = get_board_or_404(db, board_id)
    db.delete(board)
    db.commit()
