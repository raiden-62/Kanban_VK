from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import SessionLocal, init_db
from app.models import Board, BoardMember, BoardRole, Card, CardPriority, Column, Comment, Label, User


DEMO_PASSWORD = "password123"


def get_or_create_user(db, login: str) -> User:
    user = db.scalar(select(User).where(User.login == login))
    if user is not None:
        return user

    user = User(login=login, password_hash=get_password_hash(DEMO_PASSWORD))
    db.add(user)
    db.flush()
    return user


def ensure_member(db, board_id: int, user_id: int, role: BoardRole) -> None:
    membership = db.scalar(
        select(BoardMember).where(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id,
        )
    )
    if membership is None:
        db.add(BoardMember(board_id=board_id, user_id=user_id, role=role))
    else:
        membership.role = role


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        owner = get_or_create_user(db, "owner")
        editor = get_or_create_user(db, "editor")
        viewer = get_or_create_user(db, "viewer")

        board = db.scalar(select(Board).where(Board.title == "Демо-доска"))
        if board is None:
            board = Board(
                title="Демо-доска",
                description="Пример доски для демонстрации API",
                owner_id=owner.id,
            )
            db.add(board)
            db.flush()

        ensure_member(db, board.id, owner.id, BoardRole.owner)
        ensure_member(db, board.id, editor.id, BoardRole.editor)
        ensure_member(db, board.id, viewer.id, BoardRole.viewer)

        existing_columns = db.scalars(select(Column).where(Column.board_id == board.id)).all()
        if not existing_columns:
            todo = Column(board_id=board.id, title="Нужно сделать", position=0)
            progress = Column(board_id=board.id, title="В работе", position=1)
            done = Column(board_id=board.id, title="Готово", position=2, is_done=True)
            db.add_all([todo, progress, done])
            db.flush()

            backend_label = Label(board_id=board.id, title="backend", color="#2563EB")
            urgent_label = Label(board_id=board.id, title="срочно", color="#DC2626")
            db.add_all([backend_label, urgent_label])
            db.flush()

            card = Card(
                board_id=board.id,
                column_id=todo.id,
                title="Подготовить MVP",
                description="Реализовать базовый backend для Kanban-доски",
                assignee_id=editor.id,
                priority=CardPriority.high,
                position=0,
            )
            card.labels = [backend_label, urgent_label]
            db.add(card)
            db.flush()
            db.add(Comment(card_id=card.id, author_id=owner.id, text="Начинаем с backend API."))

        db.commit()
        print("Seed complete.")
        print(f"Users: owner/editor/viewer, password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
