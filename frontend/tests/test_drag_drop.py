from frontend.app.drag_drop import calculate_drop_position


def cards(*ids: int) -> list[dict]:
    return [{"id": card_id} for card_id in ids]


def test_drop_after_visible_card_uses_full_column_order() -> None:
    assert calculate_drop_position(cards(1, 2, 3), dragged_card_id=4, after_card_id=1) == 1


def test_drop_before_first_visible_card_uses_top_position() -> None:
    assert calculate_drop_position(cards(1, 2, 3), dragged_card_id=4, after_card_id=None, empty_column_position="top") == 0


def test_empty_visible_column_drops_at_end_of_full_column() -> None:
    assert calculate_drop_position(cards(1, 2, 3), dragged_card_id=4, after_card_id=None) == 3


def test_same_column_move_calculates_after_removing_dragged_card() -> None:
    assert calculate_drop_position(cards(1, 2, 3, 4), dragged_card_id=4, after_card_id=1) == 1
    assert calculate_drop_position(cards(1, 2, 3, 4), dragged_card_id=1, after_card_id=3) == 2


def test_missing_after_card_falls_back_to_end() -> None:
    assert calculate_drop_position(cards(1, 2), dragged_card_id=3, after_card_id=99) == 2
