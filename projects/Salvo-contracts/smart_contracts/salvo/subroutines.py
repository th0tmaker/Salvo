# smart_contracts/salvo/structs.py
from algopy import BoxMap, Bytes, UInt64, arc4, op, subroutine

from . import constants as cst
from . import errors as err
from . import type_aliases as ta


@subroutine
def find_valid_neighbors(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    coords: ta.GridCoords,
) -> ta.NeighborsValid:
    # Get row and col
    row, col = coords.native

    # Pre-allocate neighbors with dummy values
    neighbors = ta.Neighbors(
        ta.GridCoords((arc4.UInt8(0), arc4.UInt8(0))),
        ta.GridCoords((arc4.UInt8(0), arc4.UInt8(0))),
        ta.GridCoords((arc4.UInt8(0), arc4.UInt8(0))),
        ta.GridCoords((arc4.UInt8(0), arc4.UInt8(0))),
    )

    # Initialize a count
    count = arc4.UInt8(0)

    # Check each direction: Up, Down, Left, Right
    # Up
    if row > 0:
        new_row = arc4.UInt8(row - 1)
        if get_grid_cell_value(
            game_id, box_game_grid, convert_grid_coords_to_index(new_row, col)
        ) == arc4.UInt8(0):
            neighbors[count.native] = ta.GridCoords((new_row, col))
            count = arc4.UInt8(count.native + 1)

    # Down
    if row + 1 < cst.GRID_SIZE:
        new_row = arc4.UInt8(row + 1)
        if get_grid_cell_value(
            game_id, box_game_grid, convert_grid_coords_to_index(new_row, col)
        ) == arc4.UInt8(0):
            neighbors[count.native] = ta.GridCoords((new_row, col))
            count = arc4.UInt8(count.native + 1)

    # Left
    if col > 0:
        new_col = arc4.UInt8(col - 1)
        if get_grid_cell_value(
            game_id, box_game_grid, convert_grid_coords_to_index(row, new_col)
        ) == arc4.UInt8(0):
            neighbors[count.native] = ta.GridCoords((row, new_col))
            count = arc4.UInt8(count.native + 1)

    # Right
    if col + 1 < cst.GRID_SIZE:
        new_col = arc4.UInt8(col + 1)
        if get_grid_cell_value(
            game_id, box_game_grid, convert_grid_coords_to_index(row, new_col)
        ) == arc4.UInt8(0):
            neighbors[count.native] = ta.GridCoords((row, new_col))
            count = arc4.UInt8(count.native + 1)

    return neighbors, count


# ConvertUInt8 to 32-byte field scalar for BLS12-381 curve
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
def convert_grid_index_to_coords(i: arc4.UInt8) -> ta.GridCoords:
    # Fail transaction unless the assertion below evaluates True
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_GRID_INDEX

    # Convert game grid flattened 1D array index into 2D coordinates
    row = i.native // cst.GRID_SIZE  # Compute 'row' from integer floor division
    col = i.native % cst.GRID_SIZE  # Compute 'col' coordinate from remainder

    # Wrap coordinates in a GridCoords tuple object and return
    return ta.GridCoords((arc4.UInt8(row), arc4.UInt8(col)))


# Convert game grid row and col coords to their equivalent array index
@subroutine
def convert_grid_coords_to_index(row: arc4.UInt8, col: arc4.UInt8) -> arc4.UInt8:
    # Fail transaction unless the assertion below evaluates True
    assert (
        row.native < cst.GRID_SIZE and col.native < cst.GRID_SIZE
    ), err.INVALID_GRID_COORDS

    # Formula for mapping grid 2D coordinates (row, col) into 1D index (i)
    i = row * cst.GRID_SIZE + col  # Example: If row=3, col=2 → 3*11 + 2 = 35

    # Return index value wrapped in an UInt8 data type
    return arc4.UInt8(i)


# Get the value of a grid cell at the equivalent flattened 1D array index
@subroutine
def get_grid_cell_value(
    game_id: UInt64, box_game_grid: BoxMap[UInt64, ta.GameGrid], i: arc4.UInt8
) -> arc4.UInt8:
    # Fail transaction unless the assertion below evaluates True
    assert game_id in box_game_grid, err.GAME_ID_NOT_FOUND
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_GRID_INDEX

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
    assert i.native < cst.TOTAL_GRID_CELLS, err.INVALID_GRID_INDEX

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
