from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Label, User
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate
from app.services.labels import ensure_label_title_is_available, get_label_for_board_or_404
from app.services.permissions import require_editor, require_viewer


router = APIRouter(prefix="/tables/{board_id}/labels", tags=["labels"])


@router.get("", response_model=list[LabelRead])
def list_labels(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Label]:
    require_viewer(db, board_id, current_user)
    return db.scalars(select(Label).where(Label.board_id == board_id).order_by(Label.title, Label.id)).all()


@router.post("", response_model=LabelRead, status_code=status.HTTP_201_CREATED)
def create_label(
    board_id: int,
    payload: LabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Label:
    require_editor(db, board_id, current_user)
    ensure_label_title_is_available(db, board_id, payload.title)
    label = Label(board_id=board_id, title=payload.title, color=payload.color)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


@router.patch("/{label_id}", response_model=LabelRead)
def update_label(
    board_id: int,
    label_id: int,
    payload: LabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Label:
    require_editor(db, board_id, current_user)
    label = get_label_for_board_or_404(db, board_id, label_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "title" in update_data:
        ensure_label_title_is_available(db, board_id, update_data["title"], exclude_label_id=label.id)
    for field, value in update_data.items():
        setattr(label, field, value)
    db.commit()
    db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    board_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_editor(db, board_id, current_user)
    label = get_label_for_board_or_404(db, board_id, label_id)
    db.delete(label)
    db.commit()

