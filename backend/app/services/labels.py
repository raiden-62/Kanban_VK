from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Label


def get_label_for_board_or_404(db: Session, board_id: int, label_id: int) -> Label:
    label = db.scalar(select(Label).where(Label.id == label_id, Label.board_id == board_id))
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")
    return label


def get_labels_for_board(db: Session, board_id: int, label_ids: list[int]) -> list[Label]:
    if not label_ids:
        return []

    unique_ids = list(dict.fromkeys(label_ids))
    labels = db.scalars(
        select(Label).where(Label.board_id == board_id, Label.id.in_(unique_ids)).order_by(Label.id)
    ).all()
    if len(labels) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All labels must belong to the board",
        )
    return labels


def ensure_label_title_is_available(
    db: Session, board_id: int, title: str, exclude_label_id: int | None = None
) -> None:
    query = select(Label).where(Label.board_id == board_id, Label.title == title)
    if exclude_label_id is not None:
        query = query.where(Label.id != exclude_label_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Label title already exists")

