# smart_contracts/salvo/structs.py
from algopy import BoxMap, Bytes, UInt64, arc4, op, subroutine, urange

from . import constants as cst
from . import errors as err
from . import type_aliases as ta

# Two focused subroutines - cleaner and more efficient
# @subroutine
# def validate_move_in_neighbors(
#     neighbors_with_count: ta.NeighborsWithCount,
#     target_coords: ta.GridCoords,
# ) -> bool:
#     """Check if target coords exists in valid neighbors (early exit)"""
#     for i in urange(neighbors_with_count[1].native):
#         if neighbors_with_count[0][i] == target_coords:
#             return True
#     return False


@subroutine
def get_valid_path_cells(
    neighbors_with_count: ta.NeighborsWithCount,
) -> ta.CoordsArray:
    valid_path_cells = ta.CoordsArray()
    for i in urange(neighbors_with_count[1].native):
        coords = neighbors_with_count[0][i]
        valid_path_cells.append(coords)

    return valid_path_cells


@subroutine
def assert_coords_in_range(row: arc4.UInt8, col: arc4.UInt8) -> None:
    assert row < cst.GRID_SIZE and col < cst.GRID_SIZE, err.INVALID_POS_COORDS


@subroutine
def is_path_cell(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    row: arc4.UInt8,
    col: arc4.UInt8,
) -> bool:
    return get_grid_cell_value(
        game_id,
        box_game_grid,
        convert_grid_coords_to_index(row, col),
    ) == arc4.UInt8(0)


# Find every valid path cell that neighbors current position coords
@subroutine
def find_neighbors_with_count(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    coords: ta.CoordsPair,
) -> ta.NeighborsWithCount:
    # Initialize neighbors array with zero-coordinate placeholders
    placeholder_coords = ta.CoordsPair((arc4.UInt8(0), arc4.UInt8(0)))
    neighbors = ta.Neighbors(
        placeholder_coords, placeholder_coords, placeholder_coords, placeholder_coords
    )

    # Extract current position coordinates (row, col) and initialize valid neighbor counter
    row, col = coords.native
    count = arc4.UInt8(0)

    # North: (row > 0) ensures row value isn't going below zero (out of grid bounds when moving North)
    if (
        row > 0
        and is_path_cell(  # 'is_path_cell' checks if North neighbor is a valid path cell
            game_id, box_game_grid, arc4.UInt8(row.native - 1), col
        )
    ):
        # Overwrite placeholder coords w/ valid North neighbor coords (row-1, col) at current count index
        neighbors[count.native] = ta.CoordsPair((arc4.UInt8(row.native - 1), col))
        count = arc4.UInt8(count.native + 1)  # Increment count by 1

    # South: (row+1 < GRID_SIZE) ensures row value isn't going above GRIZ_SIZE (out of grid bounds when moving South)
    if (
        row.native + 1 < cst.GRID_SIZE
        and is_path_cell(  # 'is_path_cell' checks if South neighbor is a valid path cell
            game_id, box_game_grid, arc4.UInt8(row.native + 1), col
        )
    ):
        # Overwrite placeholder coords w/ valid South neighbor coords (row+1, col) at current count index
        neighbors[count.native] = ta.CoordsPair((arc4.UInt8(row.native + 1), col))
        count = arc4.UInt8(count.native + 1)  # Increment count by 1

    # West: (col > 0) ensures col value isn't going below zero (out of grid bounds when moving West)
    if (
        col > 0
        and is_path_cell(  # 'is_path_cell' checks if West neighbor is a valid path cell
            game_id, box_game_grid, row, arc4.UInt8(col.native - 1)
        )
    ):
        # Overwrite placeholder coords w/ valid West neighbor coords (row, col-1) at current count index
        neighbors[count.native] = ta.CoordsPair((row, arc4.UInt8(col.native - 1)))
        count = arc4.UInt8(count.native + 1)  # Increment count by 1

    # East: (col+1 < GRID_SIZE) ensures col value isn't going above GRIZ_SIZE (out of grid bounds when moving East)
    if (
        col.native + 1 < cst.GRID_SIZE
        and is_path_cell(  # 'is_path_cell' checks if East neighbor is a valid path cell
            game_id, box_game_grid, row, arc4.UInt8(col.native + 1)
        )
    ):
        # Overwrite placeholder coords w/ valid East neighbor coords (row, col+1) at current count index
        neighbors[count.native] = ta.CoordsPair((row, arc4.UInt8(col.native + 1)))
        count = arc4.UInt8(count.native + 1)

    # Return tuple implicitly w/ a copy of neighbors array and the count variable
    return neighbors.copy(), count


# Convert UInt8 to 32-byte field scalar for BLS12-381 curve
@subroutine
def u8_to_fr32(u: arc4.UInt8) -> Bytes:
    # Return big-endian byte array (AVM type: Bytes), UInt8 left-padded w/ zeros to match 32-byte scalar format
    return op.bzero(31) + u.bytes


# Convert UInt64 to 32-byte field scalar for BLS12-381 curve
@subroutine
def u64_to_fr32(u: arc4.UInt64) -> Bytes:
    # Return big-endian byte array (AVM type: Bytes), UInt64 left-padded w/ zeros to match 32-byte scalar format
    return op.bzero(24) + u.bytes


# Convert game grid array index to its equivalent row and col coordinates
@subroutine
def convert_grid_index_to_coords(i: arc4.UInt8) -> ta.CoordsPair:
    # Fail transaction unless the assertion below evaluates True
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_POS_INDEX

    # Convert game grid flattened 1D array index into 2D coordinates
    row = i.native // cst.GRID_SIZE  # Compute 'row' from integer floor division
    col = i.native % cst.GRID_SIZE  # Compute 'col' coordinate from remainder

    # Wrap coordinates in a GridCoords tuple object and return
    return ta.CoordsPair((arc4.UInt8(row), arc4.UInt8(col)))


# Convert game grid row and col coords to their equivalent array index
@subroutine
def convert_grid_coords_to_index(row: arc4.UInt8, col: arc4.UInt8) -> arc4.UInt8:
    # Formula for mapping grid 2D coordinates (row, col) into 1D index (i)
    i = (
        row.native * cst.GRID_SIZE + col.native
    )  # Example: If row=3, col=2 → 3*11 + 2 = 35

    # Return index value wrapped in an UInt8 data type
    return arc4.UInt8(i)


# Get the value of a grid cell at the equivalent flattened 1D array index
@subroutine
def get_grid_cell_value(
    game_id: UInt64, box_game_grid: BoxMap[UInt64, ta.GameGrid], i: arc4.UInt8
) -> arc4.UInt8:
    # Fail transaction unless the assertion below evaluates True
    assert game_id in box_game_grid, err.GAME_ID_NOT_FOUND
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_POS_INDEX

    # Access the game grid box contents, at the given index, and return the byte value
    return box_game_grid[game_id][i.native]


# Set the value of a grid cell at the equivalent flattened 1D array index
@subroutine
def set_grid_cell_value_at_index(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    i: arc4.UInt8,
    value: arc4.UInt8,
) -> None:
    # Fail transaction unless the assertion below evaluates True
    assert game_id in box_game_grid, err.BOX_NOT_FOUND
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_POS_INDEX

    # Access the game grid box contents, at the given index, and update the byte value
    box_game_grid[game_id][i.native] = value


# Set the value of a grid cell at the equivalent x and y coordinates
@subroutine
def set_grid_cell_value_at_coords(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    row: arc4.UInt8,
    col: arc4.UInt8,
    value: arc4.UInt8,
) -> None:
    set_grid_cell_value_at_index(
        game_id, box_game_grid, convert_grid_coords_to_index(row, col), value
    )
