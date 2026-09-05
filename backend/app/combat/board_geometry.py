from __future__ import annotations

BOARD_COLUMNS = 3
BOARD_ROWS = 2
MAX_BOARD_SLOTS = BOARD_COLUMNS * BOARD_ROWS


def column_for_slot(slot_index: int) -> int:
    if not 0 <= slot_index < MAX_BOARD_SLOTS:
        raise ValueError("slot index out of range")
    return slot_index % BOARD_COLUMNS


def row_for_slot(slot_index: int) -> int:
    if not 0 <= slot_index < MAX_BOARD_SLOTS:
        raise ValueError("slot index out of range")
    return slot_index // BOARD_COLUMNS


def slots_in_column(column: int, slot_count: int = MAX_BOARD_SLOTS) -> tuple[int, ...]:
    if not 0 <= column < BOARD_COLUMNS:
        raise ValueError("column out of range")
    if not 0 <= slot_count <= MAX_BOARD_SLOTS:
        raise ValueError("slot count out of range")
    return tuple(index for index in range(slot_count) if column_for_slot(index) == column)
