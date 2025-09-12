# smart_contracts/salvo/structs.py
from algopy import BoxMap, UInt64, arc4, subroutine

# from smart_contracts.salvo.contract import GameGrid
from . import constants as cst
from . import errors as err
from . import type_aliases as ta


# Convert the game grid array index to x and y coordinates
@subroutine
def convert_grid_index_to_coords(i: arc4.UInt8) -> ta.GridCoords:
    # Fail transaction unless the assertion below evaluates True
    assert i.native < cst.GRID_SIZE * cst.GRID_SIZE, err.INVALID_GRID_INDEX

    # Convert game grid flattened 1D array index into 2D coordinates
    y = i.native // cst.GRID_SIZE  # Compute 'y' coordinate from integer floor division
    x = i.native % cst.GRID_SIZE  # Compute 'x' coordinate from remainder

    # Wrap coordinates in a GridCoords named tuple object and return
    return ta.GridCoords(x, y)


# Convert the game grid x and y coordinates to array index
@subroutine
def convert_grid_coords_to_index(x: arc4.UInt8, y: arc4.UInt8) -> arc4.UInt8:
    # Fail transaction unless the assertion below evaluates True
    assert (
        x.native < cst.GRID_SIZE and y.native < cst.GRID_SIZE
    ), err.INVALID_GRID_COORDS

    # Formula for mapping grid 2D coordinates (x, y) into 1D index (i)
    i = y.native * cst.GRID_SIZE + x.native  # Example: If x=3, y=2 → 2*12 + 3 = 27

    # Return index value wrapped in an UInt8 data type
    return arc4.UInt8(i)


# Get the value of a grid cell at the corresponding flattened 1D array index
@subroutine
def get_grid_cell_value(
    game_id: UInt64, box_game_grid: BoxMap[UInt64, ta.GameGrid], i: arc4.UInt8
) -> arc4.UInt8:
    # Fail transaction unless the assertion below evaluates True
    assert game_id in box_game_grid, err.GAME_ID_NOT_FOUND
    assert i.native < cst.GRID_SIZE * cst.GRID_SIZE, err.INVALID_GRID_INDEX

    # Access the game grid box contents, at the given index, and return the byte value
    return box_game_grid[game_id][i.native]


# Set the value of a grid cell at the corresponding flattened 1D array index
@subroutine
def set_grid_cell_value_at_index(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    i: arc4.UInt8,
    value: arc4.UInt8,
) -> None:
    # Fail transaction unless the assertion below evaluates True
    assert game_id in box_game_grid, err.BOX_NOT_FOUND
    assert i.native < cst.GRID_SIZE * cst.GRID_SIZE, err.INVALID_GRID_INDEX

    # Access the game grid box contents, at the given index, and update the byte value
    box_game_grid[game_id][i.native] = value


# Set the value of a grid cell at the corresponding x and y coordinates
@subroutine
def set_grid_cell_value_at_coords(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    x: arc4.UInt8,
    y: arc4.UInt8,
    value: arc4.UInt8,
) -> None:
    set_grid_cell_value_at_index(
        game_id, box_game_grid, convert_grid_coords_to_index(x, y), value
    )
