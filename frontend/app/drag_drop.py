from __future__ import annotations


def calculate_drop_position(
    full_column_cards: list[dict],
    dragged_card_id: int,
    after_card_id: int | None,
    *,
    empty_column_position: str = "end",
) -> int:
    cards_without_dragged = [card for card in full_column_cards if card["id"] != dragged_card_id]

    if after_card_id is None:
        return len(cards_without_dragged) if empty_column_position == "end" else 0

    for index, card in enumerate(cards_without_dragged):
        if card["id"] == after_card_id:
            return index + 1
    return len(cards_without_dragged)
