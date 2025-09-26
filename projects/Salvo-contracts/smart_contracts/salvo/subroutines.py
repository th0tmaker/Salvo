# smart_contracts/salvo/structs.py
from algopy import Account, BoxMap, BoxRef, Bytes, UInt64, arc4, op, subroutine, urange

from . import constants as cst
from . import errors as err
from . import type_aliases as ta


# Reusable assert function: Fail transaction if row and col values are out of bounds
@subroutine
def assert_coords_in_range(row: arc4.UInt8, col: arc4.UInt8) -> None:
    assert row < cst.GRID_SIZE and col < cst.GRID_SIZE, err.INVALID_POS_COORDS


# Return a dynamic array containing all valid path cells based
@subroutine
def get_valid_path_cells(
    neighbors_with_count: ta.NeighborsWithCount,
) -> ta.CoordsArray:
    # Create a dynamic array to store multiple tuples of coords
    valid_path_cells = ta.CoordsArray()

    # Iterate through the count value of the `neighbors_with_count` tuple
    for i in urange(neighbors_with_count[1].native):
        # Every index within count range is a valid path cell, append it
        valid_path_cells.append(neighbors_with_count[0][i])

    # Return the dynamic array of valid path cells
    return valid_path_cells


# Check if character single move is valid
@subroutine
def is_single_move_valid(
    neighbors_with_count: ta.NeighborsWithCount,
    coords: ta.CoordsPair,
) -> bool:
    # Iterate through the count value of the `neighbors_with_count` tuple
    for i in urange(neighbors_with_count[1].native):
        # Check if the coords argument is equal to the neighbors entry at given index
        if coords == neighbors_with_count[0][i]:
            return True  # Move is valid
    return False  # Move is invalid


# Check if characte rmove sequence is valid
@subroutine
def is_move_sequence_valid(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    position: ta.CoordsPair,
    movement: ta.CoordsArray,
) -> bool:
    # Iterate through the coords in the movement sequence
    for coords in movement:
        # Extract row and column values from the entry
        row, col = coords.native

        # Assert row and column are within valid range
        assert_coords_in_range(row, col)

        # Get all neighbors of current position and a valid path count
        neighbors_with_count = get_neighbors_with_count(
            game_id,
            box_game_grid,
            position,
        )

        # Check if coords entry from movement sequence is not a valid move
        if not is_single_move_valid(neighbors_with_count, coords):
            return False

        # Update current position coords
        position = coords

    # If all entry coords in movement in range of count are valid, return True
    return True


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


# Get every cell that neighbors current position coords and a count of valid paths cells
@subroutine
def get_neighbors_with_count(
    game_id: UInt64,
    box_game_grid: BoxMap[UInt64, ta.GameGrid],
    position: ta.CoordsPair,
) -> ta.NeighborsWithCount:
    # Initialize neighbors array with placeholder coords (use 255 as padding value)
    placeholder_coords = ta.CoordsPair((arc4.UInt8(255), arc4.UInt8(255)))
    neighbors = ta.Neighbors(
        placeholder_coords, placeholder_coords, placeholder_coords, placeholder_coords
    )

    # Extract current position coordinates (row, col) and initialize valid neighbor counter
    row, col = position.native
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

    # Wrap coordinates in a `CoordsPair` tuple object and return
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


# Check if account is an active player of a game
@subroutine
def check_acc_in_game(
    game_id: UInt64,
    account: Account,
    box_game_lobby: BoxMap[UInt64, Bytes],
    player_count: UInt64,
    clear_player: bool,  # noqa: FBT001
) -> bool:
    # Calculate total byte length to iterate over based on player count and address size
    game_lobby_length = player_count * cst.ADDRESS_SIZE

    # Initialize flag to track if account is found in game
    acc_in_game = False

    # Iterate through the lobby byte array length in 32-byte chunks (one address per chunk)
    for i in urange(0, game_lobby_length, cst.ADDRESS_SIZE):
        # Extract the 32-byte player address at start index i
        player_addr_bytes = op.extract(box_game_lobby[game_id], i, cst.ADDRESS_SIZE)

        # Check if the extracted player address bytes match up with the account bytes
        if account.bytes == player_addr_bytes:
            acc_in_game = True

            # Optionally, clear this player from the box by replacing their address with zero bytes
            if clear_player:
                game_lobby_bref = BoxRef(
                    key=box_game_lobby.key_prefix + op.itob(game_id)
                )
                game_lobby_bref.replace(i, cst.ZEROED_ADDR_BYTES)

            # Exit loop early since sender was found
            break

    # Return True if account was found in the game, else False
    return acc_in_game
