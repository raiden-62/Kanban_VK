from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import flet as ft

from frontend.app.api_client import ApiClient
from frontend.app.components.kanban import card_control, column_control
from frontend.app.main import KanbanFrontend, app_view_from_env
from frontend.app.state import AppState
from frontend.app.theme import LABEL_COLORS


def walk(control: Any) -> Iterator[Any]:
    if control is None or isinstance(control, str):
        return
    yield control

    for attr in ("content",):
        child = getattr(control, attr, None)
        if child is not None:
            yield from walk(child)

    for attr in ("controls", "items", "actions", "options"):
        children = getattr(control, attr, None)
        if children:
            for child in children:
                yield from walk(child)


def control_names(control: Any) -> set[str]:
    return {type(item).__name__ for item in walk(control)}


def app_bar_from_rendered(control: ft.Control) -> ft.Container:
    return control.controls[0]


def sample_card() -> dict[str, Any]:
    return {
        "id": 10,
        "column_id": 1,
        "title": "Task",
        "description": "Description",
        "priority": "medium",
        "deadline": None,
        "assignee_id": None,
        "assignee_removed": False,
        "labels": [],
    }


def sample_column() -> dict[str, Any]:
    return {"id": 1, "title": "Todo", "is_done": False}


def sample_board(owner_id: int = 1) -> dict[str, Any]:
    return {"id": 1, "title": "Board", "description": "Description", "owner_id": owner_id}


def make_frontend(role: str) -> KanbanFrontend:
    frontend = KanbanFrontend.__new__(KanbanFrontend)
    frontend.state = AppState()
    frontend.state.token = "token"
    frontend.state.current_board_id = 1
    frontend.state.current_user = {"id": 1, "login": "user"}
    frontend.state.kanban = {
        "board": sample_board(),
        "columns": [],
        "cards": [],
        "labels": [],
        "members": [{"user": {"id": 1, "login": "user"}, "role": role}],
    }
    frontend.focused_field_ids = set()
    frontend.poll_refresh_in_progress = False
    return frontend


class FakePage:
    def __init__(self) -> None:
        self.dialog: ft.AlertDialog | None = None
        self.update_count = 0

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        self.dialog = dialog

    def pop_dialog(self) -> None:
        self.dialog = None

    def update(self) -> None:
        self.update_count += 1


class FakeEvent:
    def __init__(self, control: Any | None = None) -> None:
        self.control = control


class RecordingApi:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.boards: list[dict[str, Any]] = []

    def list_boards(self) -> list[dict[str, Any]]:
        self.calls.append(("list_boards",))
        return self.boards

    def create_board(self, title: str, description: str | None = None) -> dict[str, Any]:
        self.calls.append(("create_board", title, description))
        return {"id": 99, "title": title, "description": description, "owner_id": 1}

    def update_board(self, board_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("update_board", board_id, payload))
        return {**payload, "id": board_id, "owner_id": 1}

    def delete_board(self, board_id: int) -> None:
        self.calls.append(("delete_board", board_id))

    def get_kanban(self, board_id: int) -> dict[str, Any]:
        self.calls.append(("get_kanban", board_id))
        return {
            "board": sample_board(),
            "columns": [sample_column()],
            "cards": [{**sample_card(), "title": "Updated"}],
            "labels": [],
            "members": [{"user": {"id": 1, "login": "user"}, "role": "editor"}],
        }

    def update_role(self, board_id: int, user_id: int, role: str) -> dict[str, Any]:
        self.calls.append(("update_role", board_id, user_id, role))
        return {"user": {"id": user_id, "login": "member"}, "role": role}

    def delete_role(self, board_id: int, user_id: int) -> None:
        self.calls.append(("delete_role", board_id, user_id))

    def move_card(self, board_id: int, card_id: int, column_id: int, position: int) -> dict[str, Any]:
        self.calls.append(("move_card", board_id, card_id, column_id, position))
        return sample_card()

    def create_column(self, board_id: int, title: str, is_done: bool = False) -> dict[str, Any]:
        self.calls.append(("create_column", board_id, title, is_done))
        return {"id": len(self.calls), "board_id": board_id, "title": title, "is_done": is_done}

    def update_card(self, board_id: int, card_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("update_card", board_id, card_id, payload))
        return {**sample_card(), **payload, "id": card_id}

    def create_label(self, board_id: int, title: str, color: str) -> dict[str, Any]:
        self.calls.append(("create_label", board_id, title, color))
        return {"id": 1, "board_id": board_id, "title": title, "color": color}


class FakeTestLoginApi:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def login(self, login: str, password: str) -> str:
        self.calls.append(("login", login, password))
        return "token"


def test_test_login_button_uses_restored_credentials() -> None:
    frontend = make_frontend("viewer")
    frontend.api = FakeTestLoginApi()
    completed: list[str] = []
    frontend.complete_login = lambda token: completed.append(token)
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_auth()
    buttons = [control for control in walk(rendered["control"]) if isinstance(control, ft.OutlinedButton)]
    buttons[0].on_click(None)

    assert frontend.api.calls == [("login", "testuser", "123123123")]
    assert completed == ["token"]


def test_api_client_uses_kanban_api_base_url(monkeypatch: Any) -> None:
    monkeypatch.setenv("KANBAN_API_BASE_URL", "http://backend:8000/api/")
    monkeypatch.setenv("API_BASE_URL", "http://ignored:8000/api")

    assert ApiClient().base_url == "http://backend:8000/api"


def test_flet_view_can_be_configured_from_environment(monkeypatch: Any) -> None:
    monkeypatch.setenv("KANBAN_FLET_VIEW", "flet_app_web")

    assert app_view_from_env() == ft.AppView.FLET_APP_WEB


def test_focus_tracking_marks_and_clears_focused_fields() -> None:
    frontend = make_frontend("editor")
    field = ft.TextField(label="Название")
    dropdown = ft.Dropdown(label="Исполнитель")
    control = ft.Column(controls=[field, dropdown])

    frontend.attach_focus_tracking(control)
    field.on_focus(FakeEvent(field))
    dropdown.on_focus(FakeEvent(dropdown))

    assert frontend.focused_field_ids == {id(field), id(dropdown)}

    field.on_blur(FakeEvent(field))
    dropdown.on_blur(FakeEvent(dropdown))

    assert frontend.focused_field_ids == set()


def test_polling_skips_refresh_when_a_field_is_focused() -> None:
    frontend = make_frontend("editor")
    frontend.api = RecordingApi()
    frontend.render_board = lambda: None
    frontend.focused_field_ids.add(123)

    frontend.poll_current_board_once()

    assert frontend.api.calls == []


def test_polling_refreshes_open_board_when_no_field_is_focused() -> None:
    frontend = make_frontend("editor")
    frontend.api = RecordingApi()
    renders: list[str] = []
    frontend.render_board = lambda: renders.append("render")

    frontend.poll_current_board_once()

    assert frontend.api.calls == [("get_kanban", 1)]
    assert frontend.state.kanban["cards"][0]["title"] == "Updated"
    assert renders == ["render"]


def test_board_list_shows_board_actions_only_for_owned_boards() -> None:
    frontend = make_frontend("owner")
    frontend.state.current_board_id = None
    frontend.state.kanban = None
    frontend.state.boards = [sample_board(owner_id=1), {**sample_board(owner_id=2), "id": 2}]
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_boards()

    controls = list(walk(rendered["control"]))
    assert sum(isinstance(control, ft.PopupMenuButton) for control in controls) == 1


def test_create_board_dialog_has_presets() -> None:
    frontend = make_frontend("owner")
    frontend.state.current_board_id = None
    frontend.state.boards = []
    frontend.page = FakePage()
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_boards()
    create_button = [
        control
        for control in walk(rendered["control"])
        if isinstance(control, ft.Button) and control.content == "Создать доску"
    ][0]
    create_button.on_click(None)

    assert frontend.page.dialog is not None
    preset = [
        control
        for control in walk(frontend.page.dialog.content)
        if isinstance(control, ft.Dropdown) and control.label == "Шаблон"
    ][0]
    assert [(option.key, option.text) for option in preset.options] == [
        ("empty", "Пустая"),
        ("features", "Фичи"),
        ("job_applications", "Отклики на вакансии"),
    ]


def test_create_board_features_preset_seeds_columns() -> None:
    frontend = make_frontend("owner")
    frontend.state.current_board_id = None
    frontend.state.boards = []
    frontend.page = FakePage()
    frontend.api = RecordingApi()
    loads: list[str] = []
    frontend.load_boards = lambda: loads.append("load")
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_boards()
    create_button = [
        control
        for control in walk(rendered["control"])
        if isinstance(control, ft.Button) and control.content == "Создать доску"
    ][0]
    create_button.on_click(None)

    assert frontend.page.dialog is not None
    fields = [control for control in walk(frontend.page.dialog.content) if isinstance(control, ft.TextField)]
    preset = [
        control
        for control in walk(frontend.page.dialog.content)
        if isinstance(control, ft.Dropdown) and control.label == "Шаблон"
    ][0]
    fields[0].value = "Roadmap"
    fields[1].value = "Product work"
    preset.value = "features"
    frontend.page.dialog.actions[1].on_click(None)

    assert frontend.api.calls == [
        ("create_board", "Roadmap", "Product work"),
        ("create_column", 99, "Не начато", False),
        ("create_column", 99, "В работе", False),
        ("create_column", 99, "На тестировании", False),
        ("create_column", 99, "Готово", True),
    ]
    assert loads == ["load"]


def test_load_boards_clears_current_board_state() -> None:
    frontend = make_frontend("owner")
    frontend.api = RecordingApi()
    frontend.state.selected_card_id = 10
    frontend.state.filters = {"q": "old"}
    frontend.render_boards = lambda: None

    frontend.load_boards()

    assert frontend.state.current_board_id is None
    assert frontend.state.kanban is None
    assert frontend.state.selected_card_id is None
    assert frontend.state.filters == {}


def test_owner_board_edit_dialog_saves_changes() -> None:
    frontend = make_frontend("owner")
    frontend.page = FakePage()
    frontend.api = RecordingApi()
    refreshes: list[str] = []
    frontend.refresh_kanban = lambda: refreshes.append("refresh")

    frontend.open_edit_board_dialog(sample_board())
    assert frontend.page.dialog is not None
    fields = [control for control in walk(frontend.page.dialog.content) if isinstance(control, ft.TextField)]
    fields[0].value = "Updated"
    fields[1].value = "New description"

    frontend.page.dialog.actions[1].on_click(None)

    assert frontend.api.calls == [("update_board", 1, {"title": "Updated", "description": "New description"})]
    assert refreshes == ["refresh"]


def test_owner_board_delete_dialog_deletes_and_clears_current_board() -> None:
    frontend = make_frontend("owner")
    frontend.page = FakePage()
    frontend.api = RecordingApi()
    loads: list[str] = []
    frontend.load_boards = lambda: loads.append("load")

    frontend.open_delete_board_dialog(sample_board())
    assert frontend.page.dialog is not None
    frontend.page.dialog.actions[1].on_click(None)

    assert frontend.api.calls == [("delete_board", 1)]
    assert frontend.state.current_board_id is None
    assert frontend.state.kanban is None
    assert frontend.state.selected_card_id is None
    assert loads == ["load"]


def test_board_screen_shows_board_actions_only_for_owner() -> None:
    frontend = make_frontend("owner")
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_board()

    app_bar = app_bar_from_rendered(rendered["control"])
    controls = list(walk(app_bar))
    assert any(isinstance(control, ft.PopupMenuButton) for control in controls)


def test_board_screen_hides_board_actions_for_viewer() -> None:
    frontend = make_frontend("viewer")
    rendered: dict[str, Any] = {}
    frontend.render = lambda control: rendered.update(control=control)

    frontend.render_board()

    app_bar = app_bar_from_rendered(rendered["control"])
    controls = list(walk(app_bar))
    assert not any(isinstance(control, ft.PopupMenuButton) for control in controls)


def test_non_owner_cannot_open_board_edit_or_delete_dialogs() -> None:
    frontend = make_frontend("viewer")
    frontend.page = FakePage()

    frontend.open_edit_board_dialog(sample_board(owner_id=2))
    frontend.open_delete_board_dialog(sample_board(owner_id=2))

    assert frontend.page.dialog is None


def test_viewer_card_control_hides_move_buttons() -> None:
    control = card_control(sample_card(), lambda _: None, can_edit=False)

    assert "IconButton" not in control_names(control)


def test_editor_card_control_hides_legacy_move_buttons() -> None:
    control = card_control(sample_card(), lambda _: None, can_edit=True)

    icons = [
        item.icon
        for item in walk(control)
        if isinstance(item, ft.IconButton)
    ]
    assert ft.Icons.CHEVRON_LEFT not in icons
    assert ft.Icons.CHEVRON_RIGHT not in icons


def test_removed_assignee_is_rendered_on_card() -> None:
    card = {**sample_card(), "assignee_removed": True}
    control = card_control(card, lambda _: None, can_edit=False)

    texts = [control.value for control in walk(control) if isinstance(control, ft.Text)]
    assert "Пользователь удален" in texts


def test_viewer_move_card_callback_does_not_call_api() -> None:
    frontend = make_frontend("viewer")
    frontend.api = RecordingApi()
    frontend.state.kanban["columns"] = [{"id": 1}, {"id": 2}]

    frontend.move_card_by_delta(sample_card(), 1)

    assert frontend.api.calls == []


def test_editor_move_card_callback_calls_api_with_target_column() -> None:
    frontend = make_frontend("editor")
    frontend.api = RecordingApi()
    frontend.state.kanban["columns"] = [{"id": 1}, {"id": 2}]
    refreshes: list[str] = []
    frontend.refresh_kanban = lambda: refreshes.append("refresh")

    frontend.move_card_by_delta(sample_card(), 1)

    assert frontend.api.calls == [("move_card", 1, 10, 2, 0)]
    assert refreshes == ["refresh"]


def test_drop_card_after_visible_card_uses_full_column_position() -> None:
    frontend = make_frontend("editor")
    frontend.api = RecordingApi()
    frontend.state.kanban["cards"] = [
        {**sample_card(), "id": 1, "column_id": 1, "position": 0},
        {**sample_card(), "id": 2, "column_id": 1, "position": 1},
        {**sample_card(), "id": 3, "column_id": 1, "position": 2},
        {**sample_card(), "id": 4, "column_id": 2, "position": 0},
    ]
    refreshes: list[str] = []
    frontend.refresh_kanban = lambda: refreshes.append("refresh")

    frontend.drop_card(dragged_card_id=4, target_column_id=1, after_card_id=1)

    assert frontend.api.calls == [("move_card", 1, 4, 1, 1)]
    assert refreshes == ["refresh"]


def test_drop_card_inside_same_column_removes_dragged_card_before_positioning() -> None:
    frontend = make_frontend("editor")
    frontend.api = RecordingApi()
    frontend.state.kanban["cards"] = [
        {**sample_card(), "id": 1, "column_id": 1, "position": 0},
        {**sample_card(), "id": 2, "column_id": 1, "position": 1},
        {**sample_card(), "id": 3, "column_id": 1, "position": 2},
        {**sample_card(), "id": 4, "column_id": 1, "position": 3},
    ]
    frontend.refresh_kanban = lambda: None

    frontend.drop_card(dragged_card_id=4, target_column_id=1, after_card_id=1)

    assert frontend.api.calls == [("move_card", 1, 4, 1, 1)]


def test_viewer_column_control_hides_add_edit_delete_controls() -> None:
    control = column_control(
        sample_column(),
        [sample_card()],
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda *_: None,
        can_edit=False,
    )

    names = control_names(control)
    assert "IconButton" not in names
    assert "PopupMenuButton" not in names
    assert not isinstance(control, ft.GestureDetector)


def test_editor_column_control_keeps_add_edit_delete_controls() -> None:
    control = column_control(
        sample_column(),
        [sample_card()],
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda *_: None,
        can_edit=True,
    )

    names = control_names(control)
    assert "IconButton" in names
    assert "PopupMenuButton" in names
    assert control.on_secondary_tap is not None


def test_editor_column_control_has_draggable_cards_and_drop_targets() -> None:
    control = column_control(
        sample_column(),
        [sample_card()],
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda _: None,
        lambda *_: None,
        can_edit=True,
    )

    controls = list(walk(control))
    assert any(isinstance(control, ft.Draggable) for control in controls)
    assert sum(isinstance(control, ft.DragTarget) for control in controls) == 2


def test_viewer_card_panel_is_read_only_and_hides_write_actions() -> None:
    frontend = make_frontend("viewer")
    frontend.load_comments_for_panel = lambda _: []

    panel = frontend.card_panel(sample_card(), [{"id": 1, "title": "Bug", "color": "#2787F5"}], [], can_edit=False)
    controls = list(walk(panel))

    assert all(not isinstance(control, ft.Button) for control in controls)
    assert all(
        getattr(control, "read_only", True)
        for control in controls
        if isinstance(control, ft.TextField)
    )
    assert all(
        getattr(control, "disabled", True)
        for control in controls
        if isinstance(control, (ft.Dropdown, ft.Checkbox))
    )


def test_removed_assignee_is_rendered_on_card_panel() -> None:
    frontend = make_frontend("viewer")
    frontend.load_comments_for_panel = lambda _: []

    panel = frontend.card_panel({**sample_card(), "assignee_removed": True}, [], [], can_edit=False)

    texts = [control.value for control in walk(panel) if isinstance(control, ft.Text)]
    assert "Пользователь удален" in texts


def test_card_panel_assignee_dropdown_lists_board_members() -> None:
    frontend = make_frontend("editor")
    frontend.state.kanban["members"].append({"user": {"id": 2, "login": "member"}, "role": "viewer"})
    frontend.load_comments_for_panel = lambda _: []

    panel = frontend.card_panel({**sample_card(), "assignee_id": 2}, [], [], can_edit=True)

    assignee = [
        control
        for control in walk(panel)
        if isinstance(control, ft.Dropdown) and control.label == "Исполнитель"
    ][0]
    assert assignee.value == "2"
    assert [(option.key, option.text) for option in assignee.options] == [
        ("none", "Без исполнителя"),
        ("1", "user (#1)"),
        ("2", "member (#2)"),
    ]


def test_card_panel_saves_selected_assignee_from_dropdown() -> None:
    frontend = make_frontend("editor")
    frontend.state.kanban["members"].append({"user": {"id": 2, "login": "member"}, "role": "viewer"})
    frontend.api = RecordingApi()
    frontend.load_comments_for_panel = lambda _: []
    refreshes: list[str] = []
    frontend.refresh_kanban = lambda: refreshes.append("refresh")

    panel = frontend.card_panel(sample_card(), [], [], can_edit=True)
    assignee = [
        control
        for control in walk(panel)
        if isinstance(control, ft.Dropdown) and control.label == "Исполнитель"
    ][0]
    assignee.value = "2"
    save_button = [
        control
        for control in walk(panel)
        if isinstance(control, ft.Button) and control.content == "Сохранить"
    ][0]
    save_button.on_click(None)

    assert frontend.api.calls == [
        (
            "update_card",
            1,
            10,
            {
                "title": "Task",
                "description": "Description",
                "assignee_id": 2,
                "deadline": None,
                "priority": "medium",
                "label_ids": [],
            },
        )
    ]
    assert refreshes == ["refresh"]


def test_non_owner_members_dialog_hides_add_member_controls() -> None:
    frontend = make_frontend("viewer")
    frontend.page = FakePage()

    frontend.open_members_dialog(None)

    assert frontend.page.dialog is not None
    controls = list(walk(frontend.page.dialog.content))
    assert len(frontend.page.dialog.actions) == 1
    assert not any(isinstance(control, ft.TextField) for control in controls)
    assert not any(isinstance(control, ft.Dropdown) for control in controls)


def test_owner_members_dialog_shows_add_member_controls() -> None:
    frontend = make_frontend("owner")
    frontend.page = FakePage()

    frontend.open_members_dialog(None)

    assert frontend.page.dialog is not None
    controls = list(walk(frontend.page.dialog.content))
    assert len(frontend.page.dialog.actions) == 2
    assert any(isinstance(control, ft.TextField) for control in controls)
    assert any(isinstance(control, ft.Dropdown) for control in controls)


def test_owner_can_edit_member_role_from_members_dialog() -> None:
    frontend = make_frontend("owner")
    frontend.state.kanban["members"].append({"user": {"id": 2, "login": "member"}, "role": "viewer"})
    frontend.page = FakePage()
    frontend.api = RecordingApi()

    frontend.open_members_dialog(None)
    assert frontend.page.dialog is not None
    member_dropdown = [
        control
        for control in walk(frontend.page.dialog.content)
        if isinstance(control, ft.Dropdown) and control.value == "viewer"
    ][0]
    member_dropdown.value = "editor"
    member_dropdown.on_change(FakeEvent(member_dropdown))

    assert frontend.api.calls == [("update_role", 1, 2, "editor")]
    assert frontend.page.update_count == 1
    dropdowns = [control for control in walk(frontend.page.dialog.content) if isinstance(control, ft.Dropdown)]
    assert any(control.value == "editor" for control in dropdowns)


def test_owner_can_remove_member_from_members_dialog() -> None:
    frontend = make_frontend("owner")
    frontend.state.kanban["members"].append({"user": {"id": 2, "login": "member"}, "role": "editor"})
    frontend.page = FakePage()
    frontend.api = RecordingApi()

    frontend.open_members_dialog(None)
    assert frontend.page.dialog is not None
    remove_button = [
        control
        for control in walk(frontend.page.dialog.content)
        if isinstance(control, ft.IconButton) and control.icon == ft.Icons.PERSON_REMOVE
    ][0]
    remove_button.on_click(None)

    assert frontend.api.calls == [("delete_role", 1, 2)]
    assert frontend.page.update_count == 1
    member_texts = [
        control.value
        for control in walk(frontend.page.dialog.content)
        if isinstance(control, ft.Text)
    ]
    assert "member" not in member_texts


def test_labels_dialog_uses_preset_color_swatches() -> None:
    frontend = make_frontend("owner")
    frontend.page = FakePage()

    frontend.open_labels_dialog(None)

    assert frontend.page.dialog is not None
    controls = list(walk(frontend.page.dialog.content))
    text_fields = [control for control in controls if isinstance(control, ft.TextField)]
    color_swatches = [
        control
        for control in controls
        if isinstance(control, ft.Container) and control.data in {item["color"] for item in LABEL_COLORS}
    ]
    assert len(text_fields) == 1
    assert not any(isinstance(control, ft.Dropdown) for control in controls)
    assert [swatch.data for swatch in color_swatches] == [item["color"] for item in LABEL_COLORS]
    assert color_swatches[0].border.top.width == 3
    assert isinstance(color_swatches[0].content, ft.Icon)
    assert color_swatches[1].border.top.width == 1
    assert color_swatches[1].content is None


def test_labels_dialog_sends_clicked_swatch_color() -> None:
    frontend = make_frontend("owner")
    frontend.page = FakePage()
    frontend.api = RecordingApi()
    refreshes: list[str] = []
    frontend.refresh_kanban = lambda: refreshes.append("refresh")

    frontend.open_labels_dialog(None)

    assert frontend.page.dialog is not None
    controls = list(walk(frontend.page.dialog.content))
    title = [control for control in controls if isinstance(control, ft.TextField)][0]
    title.value = "feature"
    color_swatches = [
        control
        for control in controls
        if isinstance(control, ft.Container) and control.data in {item["color"] for item in LABEL_COLORS}
    ]
    color_swatches[2].on_click(None)
    frontend.page.dialog.actions[1].on_click(None)

    assert color_swatches[0].border.top.width == 1
    assert color_swatches[0].content is None
    assert color_swatches[2].border.top.width == 3
    assert isinstance(color_swatches[2].content, ft.Icon)
    assert frontend.api.calls == [("create_label", 1, "feature", LABEL_COLORS[2]["color"])]
    assert refreshes == ["refresh"]
