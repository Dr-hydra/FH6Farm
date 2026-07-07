VALID_DIRECTIONS = {"up", "down", "left", "right"}
START_CELL = 12
GRID_SIZE = 4


def move_cell(current, direction):
    direction = str(direction or "").strip().lower()
    row = current // GRID_SIZE
    col = current % GRID_SIZE

    if direction == "up":
        row -= 1
    elif direction == "down":
        row += 1
    elif direction == "left":
        col -= 1
    elif direction == "right":
        col += 1
    else:
        return None

    if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
        return None
    return row * GRID_SIZE + col


def directions_to_cells(directions, start_cell=START_CELL, allow_revisit=False):
    cells = [start_cell]
    normalized = []
    seen = {start_cell}
    current = start_cell

    for raw_direction in directions or []:
        direction = str(raw_direction or "").strip().lower()
        if direction not in VALID_DIRECTIONS:
            continue

        next_cell = move_cell(current, direction)
        if next_cell is None:
            break
        if not allow_revisit and next_cell in seen:
            break

        cells.append(next_cell)
        normalized.append(direction)
        seen.add(next_cell)
        current = next_cell

    return cells, normalized


def cells_to_directions(cells):
    cells = list(cells or [])
    if len(cells) <= 1:
        return []

    directions = []
    for previous, current in zip(cells, cells[1:]):
        row_change = current // GRID_SIZE - previous // GRID_SIZE
        column_change = current % GRID_SIZE - previous % GRID_SIZE
        if row_change == -1 and column_change == 0:
            directions.append("up")
        elif row_change == 1 and column_change == 0:
            directions.append("down")
        elif row_change == 0 and column_change == -1:
            directions.append("left")
        elif row_change == 0 and column_change == 1:
            directions.append("right")
        else:
            break
    return directions


def normalize_skill_dirs(directions):
    return directions_to_cells(directions)[1]
