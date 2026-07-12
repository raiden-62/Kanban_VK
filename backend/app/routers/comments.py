from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import BoardRole, Comment, User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services.permissions import (
    get_card_for_board_or_404,
    get_membership,
    require_editor,
    require_viewer,
)


router = APIRouter(prefix="/tables/{board_id}/cards/{card_id}/comments", tags=["comments"])


def _get_comment_or_404(db: Session, card_id: int, comment_id: int) -> Comment:
    comment = db.scalar(select(Comment).where(Comment.id == comment_id, Comment.card_id == card_id))
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


def _ensure_comment_owner_or_board_owner(
    db: Session, board_id: int, comment: Comment, current_user: User
) -> None:
    membership = get_membership(db, board_id, current_user.id)
    if comment.author_id == current_user.id:
        return
    if membership is not None and membership.role == BoardRole.owner:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


@router.get("", response_model=list[CommentRead])
def list_comments(
    board_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Comment]:
    require_viewer(db, board_id, current_user)
    get_card_for_board_or_404(db, board_id, card_id)
    return db.scalars(
        select(Comment).where(Comment.card_id == card_id).order_by(Comment.created_at, Comment.id)
    ).all()


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    board_id: int,
    card_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Comment:
    require_editor(db, board_id, current_user)
    get_card_for_board_or_404(db, board_id, card_id)
    comment = Comment(card_id=card_id, author_id=current_user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    board_id: int,
    card_id: int,
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Comment:
    require_editor(db, board_id, current_user)
    get_card_for_board_or_404(db, board_id, card_id)
    comment = _get_comment_or_404(db, card_id, comment_id)
    _ensure_comment_owner_or_board_owner(db, board_id, comment, current_user)
    comment.text = payload.text
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    board_id: int,
    card_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_editor(db, board_id, current_user)
    get_card_for_board_or_404(db, board_id, card_id)
    comment = _get_comment_or_404(db, card_id, comment_id)
    _ensure_comment_owner_or_board_owner(db, board_id, comment, current_user)
    db.delete(comment)
    db.commit()

