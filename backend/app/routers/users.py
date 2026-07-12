from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def search_users(
    q: str = Query(default="", max_length=64),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    query = select(User)
    if q:
        query = query.where(User.login.ilike(f"%{q.strip()}%"))
    return db.scalars(query.order_by(User.login).limit(limit)).all()
