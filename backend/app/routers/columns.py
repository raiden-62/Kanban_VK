from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Column, User
from app.schemas.column import ColumnCreate, ColumnRead, ColumnUpdate
from app.services.ordering import insert_column, normalize_column_positions
from app.services.permissions import get_column_for_board_or_404, require_editor, require_viewer


router = APIRouter(prefix="/tables/{board_id}/columns", tags=["columns"])


@router.get("", response_model=list[ColumnRead])
def list_columns(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Column]:
    require_viewer(db, board_id, current_user)
    return db.scalars(
        select(Column).where(Column.board_id == board_id).order_by(Column.position, Column.id)
    ).all()


@router.post("", response_model=ColumnRead, status_code=status.HTTP_201_CREATED)
def create_column(
    board_id: int,
    payload: ColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Column:
    require_editor(db, board_id, current_user)
    column = Column(board_id=board_id, title=payload.title, is_done=payload.is_done, position=0)
    db.add(column)
    insert_column(db, column, payload.position)
    db.commit()
    db.refresh(column)
    return column


@router.patch("/{column_id}", response_model=ColumnRead)
def update_column(
    board_id: int,
    column_id: int,
    payload: ColumnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Column:
    require_editor(db, board_id, current_user)
    column = get_column_for_board_or_404(db, board_id, column_id)
    if payload.title is not None:
        column.title = payload.title
    if payload.is_done is not None:
        column.is_done = payload.is_done
    if payload.position is not None:
        columns = db.scalars(
            select(Column)
            .where(Column.board_id == board_id, Column.id != column.id)
            .order_by(Column.position, Column.id)
        ).all()
        columns.insert(min(payload.position, len(columns)), column)
        for index, existing_column in enumerate(columns):
            existing_column.position = index
    db.commit()
    db.refresh(column)
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(
    board_id: int,
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_editor(db, board_id, current_user)
    column = get_column_for_board_or_404(db, board_id, column_id)
    db.delete(column)
    db.flush()
    normalize_column_positions(db, board_id)
    db.commit()
