from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal, init_db
from app.models import Board, BoardMember, BoardRole, Card, CardPriority, Column, Label, User


DEMO_PASSWORD = "password123"


@dataclass(frozen=True)
class LabelSpec:
    title: str
    color: str


@dataclass(frozen=True)
class ColumnSpec:
    title: str
    is_done: bool = False


@dataclass(frozen=True)
class CardSpec:
    title: str
    column: str
    assignee: str
    deadline_offset_days: int
    priority: CardPriority
    labels: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class BoardSpec:
    title: str
    description: str
    columns: tuple[ColumnSpec, ...]
    labels: tuple[LabelSpec, ...]
    cards: tuple[CardSpec, ...]


DEMO_USERS = {
    "demo_owner": BoardRole.owner,
    "demo_editor": BoardRole.editor,
    "demo_viewer": BoardRole.viewer,
    "demo_hr": BoardRole.editor,
    "demo_tech": BoardRole.editor,
}


FEATURE_BOARD = BoardSpec(
    title="Демо: Фичи",
    description="Пример продуктовой доски с фичами, тестированием и релизными задачами.",
    columns=(
        ColumnSpec("Не начато"),
        ColumnSpec("В работе"),
        ColumnSpec("На тестировании"),
        ColumnSpec("Готово", is_done=True),
    ),
    labels=(
        LabelSpec("frontend", "#2787F5"),
        LabelSpec("backend", "#4BB34B"),
        LabelSpec("bug", "#E64646"),
        LabelSpec("ux", "#9B59B6"),
        LabelSpec("release", "#F2994A"),
    ),
    cards=(
        CardSpec(
            "Добавить шаблоны досок",
            "Готово",
            "demo_editor",
            -5,
            CardPriority.medium,
            ("frontend", "ux"),
            "Пользователь выбирает шаблон при создании новой доски.",
        ),
        CardSpec(
            "Настроить drag and drop карточек",
            "Готово",
            "demo_tech",
            -3,
            CardPriority.high,
            ("frontend",),
            "Карточки перемещаются между колонками и сохраняют порядок.",
        ),
        CardSpec(
            "Сделать фоновое обновление доски",
            "На тестировании",
            "demo_editor",
            1,
            CardPriority.high,
            ("frontend", "release"),
            "Клиент обновляет доску каждую секунду, если пользователь не редактирует поле.",
        ),
        CardSpec(
            "Проверить права viewer",
            "На тестировании",
            "demo_viewer",
            2,
            CardPriority.medium,
            ("backend",),
            "Viewer не должен видеть кнопки изменения доски, колонок и карточек.",
        ),
        CardSpec(
            "Исправить отображение удаленного исполнителя",
            "В работе",
            "demo_tech",
            3,
            CardPriority.high,
            ("backend", "bug"),
            "После удаления участника карточки показывают, что пользователь удален.",
        ),
        CardSpec(
            "Добавить фильтр по просроченным",
            "В работе",
            "demo_editor",
            -1,
            CardPriority.critical,
            ("frontend", "bug"),
            "Просроченные карточки должны выделяться в баннере.",
        ),
        CardSpec(
            "Подготовить smoke-сценарий API",
            "В работе",
            "demo_tech",
            4,
            CardPriority.medium,
            ("backend", "release"),
            "Скрипт проверяет регистрацию, доски, колонки, карточки и комментарии.",
        ),
        CardSpec(
            "Добавить компактную карточку меток",
            "Не начато",
            "demo_editor",
            5,
            CardPriority.low,
            ("frontend", "ux"),
            "В карточке показываются первые несколько меток.",
        ),
        CardSpec(
            "Проверить Docker compose",
            "Не начато",
            "demo_owner",
            6,
            CardPriority.high,
            ("release",),
            "Backend и frontend запускаются отдельными сервисами.",
        ),
        CardSpec(
            "Описать модель авторизации",
            "Не начато",
            "demo_owner",
            7,
            CardPriority.medium,
            ("backend",),
            "Для защиты нужно объяснить JWT, хэширование паролей и роли.",
        ),
        CardSpec(
            "Улучшить пустые состояния",
            "Не начато",
            "demo_editor",
            9,
            CardPriority.low,
            ("ux",),
            "Пустые доски и колонки должны выглядеть аккуратно.",
        ),
        CardSpec(
            "Проверить порядок карточек при фильтрах",
            "Не начато",
            "demo_tech",
            10,
            CardPriority.medium,
            ("frontend", "bug"),
            "Drop при активном фильтре вставляет карточку после видимой карточки в полном списке.",
        ),
    ),
)


HIRING_BOARD = BoardSpec(
    title="Демо: Найм",
    description="Пример доски для отслеживания откликов и собеседований.",
    columns=(
        ColumnSpec("Резюме не рассмотрено"),
        ColumnSpec("HR-интервью"),
        ColumnSpec("Техническое интервью"),
        ColumnSpec("Принят", is_done=True),
    ),
    labels=(
        LabelSpec("backend", "#4BB34B"),
        LabelSpec("frontend", "#2787F5"),
        LabelSpec("junior", "#7F8C8D"),
        LabelSpec("middle", "#F2994A"),
        LabelSpec("urgent", "#E64646"),
    ),
    cards=(
        CardSpec(
            "Анна Кузнецова",
            "Принят",
            "demo_hr",
            -7,
            CardPriority.high,
            ("frontend", "middle"),
            "Принята на позицию frontend-разработчика.",
        ),
        CardSpec(
            "Иван Петров",
            "Техническое интервью",
            "demo_tech",
            1,
            CardPriority.critical,
            ("backend", "urgent"),
            "Назначить live coding и проверить опыт с FastAPI.",
        ),
        CardSpec(
            "Мария Смирнова",
            "Техническое интервью",
            "demo_tech",
            2,
            CardPriority.high,
            ("frontend", "middle"),
            "Кандидат хорошо прошел HR-интервью, нужен технический этап.",
        ),
        CardSpec(
            "Дмитрий Соколов",
            "HR-интервью",
            "demo_hr",
            -1,
            CardPriority.high,
            ("backend", "urgent"),
            "Просрочен первичный созвон, нужно переназначить.",
        ),
        CardSpec(
            "Елена Волкова",
            "HR-интервью",
            "demo_hr",
            3,
            CardPriority.medium,
            ("frontend", "junior"),
            "Уточнить ожидания по стажировке и графику.",
        ),
        CardSpec(
            "Павел Морозов",
            "HR-интервью",
            "demo_hr",
            4,
            CardPriority.medium,
            ("backend", "middle"),
            "Есть коммерческий опыт с SQLAlchemy.",
        ),
        CardSpec(
            "Ольга Васильева",
            "Резюме не рассмотрено",
            "demo_hr",
            5,
            CardPriority.low,
            ("frontend", "junior"),
            "Нужно проверить портфолио и учебные проекты.",
        ),
        CardSpec(
            "Сергей Новиков",
            "Резюме не рассмотрено",
            "demo_tech",
            6,
            CardPriority.medium,
            ("backend",),
            "Посмотреть опыт с Docker и REST API.",
        ),
        CardSpec(
            "Наталья Федорова",
            "Резюме не рассмотрено",
            "demo_hr",
            7,
            CardPriority.medium,
            ("frontend", "middle"),
            "Проверить релевантность опыта с UI-компонентами.",
        ),
        CardSpec(
            "Алексей Орлов",
            "Резюме не рассмотрено",
            "demo_tech",
            8,
            CardPriority.low,
            ("backend", "junior"),
            "Первый коммерческий опыт, нужно оценить базу Python.",
        ),
        CardSpec(
            "Кирилл Егоров",
            "Техническое интервью",
            "demo_tech",
            -2,
            CardPriority.critical,
            ("backend", "middle", "urgent"),
            "Техническое интервью просрочено, требуется решение по кандидату.",
        ),
        CardSpec(
            "Виктория Павлова",
            "HR-интервью",
            "demo_hr",
            10,
            CardPriority.medium,
            ("frontend",),
            "Назначить первичный звонок на следующую неделю.",
        ),
    ),
)


def get_or_create_user(db: Session, login: str) -> User:
    user = db.scalar(select(User).where(User.login == login))
    if user is not None:
        return user

    user = User(login=login, password_hash=get_password_hash(DEMO_PASSWORD))
    db.add(user)
    db.flush()
    return user


def ensure_member(db: Session, board_id: int, user_id: int, role: BoardRole) -> None:
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


def create_demo_board(db: Session, spec: BoardSpec, users: dict[str, User]) -> bool:
    existing_board = db.scalar(select(Board).where(Board.title == spec.title))
    if existing_board is not None:
        print(f"Skipped existing board: {spec.title}")
        return False

    board = Board(title=spec.title, description=spec.description, owner_id=users["demo_owner"].id)
    db.add(board)
    db.flush()

    for login, role in DEMO_USERS.items():
        ensure_member(db, board.id, users[login].id, role)

    columns_by_title: dict[str, Column] = {}
    for position, column_spec in enumerate(spec.columns):
        column = Column(
            board_id=board.id,
            title=column_spec.title,
            position=position,
            is_done=column_spec.is_done,
        )
        db.add(column)
        columns_by_title[column.title] = column
    db.flush()

    labels_by_title: dict[str, Label] = {}
    for label_spec in spec.labels:
        label = Label(board_id=board.id, title=label_spec.title, color=label_spec.color)
        db.add(label)
        labels_by_title[label.title] = label
    db.flush()

    positions_by_column: dict[str, int] = {column.title: 0 for column in columns_by_title.values()}
    today = date.today()
    for card_spec in spec.cards:
        column = columns_by_title[card_spec.column]
        card = Card(
            board_id=board.id,
            column_id=column.id,
            title=card_spec.title,
            description=card_spec.description,
            assignee_id=users[card_spec.assignee].id,
            deadline=today + timedelta(days=card_spec.deadline_offset_days),
            priority=card_spec.priority,
            position=positions_by_column[column.title],
        )
        positions_by_column[column.title] += 1
        card.labels = [labels_by_title[label_title] for label_title in card_spec.labels]
        db.add(card)

    print(f"Created board: {spec.title}")
    return True


def seed_mock_data(db: Session) -> int:
    users = {login: get_or_create_user(db, login) for login in DEMO_USERS}
    created_count = 0
    for spec in (FEATURE_BOARD, HIRING_BOARD):
        if create_demo_board(db, spec, users):
            created_count += 1
    return created_count


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        created_count = seed_mock_data(db)
        db.commit()
        print(f"Mock data seed complete. Created boards: {created_count}")
        print(f"Demo users: {', '.join(DEMO_USERS)}")
        print(f"Password for all demo users: {DEMO_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
