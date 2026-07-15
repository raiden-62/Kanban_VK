from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import BoardMember, BoardRole, Card, User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.permissions import get_membership, require_owner, require_viewer


router = APIRouter(prefix="/tables/{board_id}/roles", tags=["roles"])


def _ensure_manageable_role(role: BoardRole) -> None:
    if role == BoardRole.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner role is assigned when the board is created",
        )


@router.get("", response_model=list[RoleRead])
def list_roles(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BoardMember]:
    require_viewer(db, board_id, current_user)
    return db.scalars(
        select(BoardMember)
        .options(joinedload(BoardMember.user))
        .where(BoardMember.board_id == board_id)
        .order_by(BoardMember.id)
    ).all()


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def add_role(
    board_id: int,
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardMember:
    require_owner(db, board_id, current_user)
    _ensure_manageable_role(payload.role)

    user = db.scalar(select(User).where(User.login == payload.login))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if get_membership(db, board_id, user.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has a role")

    membership = BoardMember(board_id=board_id, user_id=user.id, role=payload.role)
    db.add(membership)
    db.commit()
    return db.scalar(
        select(BoardMember).options(joinedload(BoardMember.user)).where(BoardMember.id == membership.id)
    )


@router.patch("/{user_id}", response_model=RoleRead)
def update_role(
    board_id: int,
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardMember:
    require_owner(db, board_id, current_user)
    _ensure_manageable_role(payload.role)

    membership = get_membership(db, board_id, user_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if membership.role == BoardRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Board owner cannot be changed")

    membership.role = payload.role
    db.commit()
    return db.scalar(
        select(BoardMember).options(joinedload(BoardMember.user)).where(BoardMember.id == membership.id)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    board_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_owner(db, board_id, current_user)
    membership = get_membership(db, board_id, user_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if membership.role == BoardRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Board owner cannot be removed")

    db.execute(
        update(Card)
        .where(Card.board_id == board_id, Card.assignee_id == user_id)
        .values(assignee_id=None, assignee_removed=True)
    )
    db.delete(membership)
    db.commit()
