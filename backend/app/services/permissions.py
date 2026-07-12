from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Board, BoardMember, BoardRole, Card, Column, User


ROLE_LEVEL = {
    BoardRole.viewer: 1,
    BoardRole.editor: 2,
    BoardRole.owner: 3,
}


def get_board_or_404(db: Session, board_id: int) -> Board:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return board


def get_membership(db: Session, board_id: int, user_id: int) -> BoardMember | None:
    return db.scalar(
        select(BoardMember).where(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id,
        )
    )


def require_role(db: Session, board_id: int, user: User, minimum_role: BoardRole) -> BoardMember:
    get_board_or_404(db, board_id)
    membership = get_membership(db, board_id, user.id)
    if membership is None or ROLE_LEVEL[membership.role] < ROLE_LEVEL[minimum_role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return membership


def require_owner(db: Session, board_id: int, user: User) -> BoardMember:
    return require_role(db, board_id, user, BoardRole.owner)


def require_editor(db: Session, board_id: int, user: User) -> BoardMember:
    return require_role(db, board_id, user, BoardRole.editor)


def require_viewer(db: Session, board_id: int, user: User) -> BoardMember:
    return require_role(db, board_id, user, BoardRole.viewer)


def get_column_for_board_or_404(db: Session, board_id: int, column_id: int) -> Column:
    column = db.scalar(select(Column).where(Column.id == column_id, Column.board_id == board_id))
    if column is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return column


def get_card_for_board_or_404(db: Session, board_id: int, card_id: int) -> Card:
    card = db.scalar(select(Card).where(Card.id == card_id, Card.board_id == board_id))
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


def ensure_user_is_board_member(db: Session, board_id: int, user_id: int | None) -> None:
    if user_id is None:
        return
    if get_membership(db, board_id, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a board member",
        )

