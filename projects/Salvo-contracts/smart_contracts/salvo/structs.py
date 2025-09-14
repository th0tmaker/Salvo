# smart_contracts/salvo/structs.py
from algopy import arc4


# Define a struct that will store the user registry object data
class UserRegistry(arc4.Struct):
    hosting_game: arc4.Bool  # Track if user is already hosting a game
    game_id: arc4.UInt64  # Game ID user has made a commitment towards playing
    commit_rand_round: arc4.UInt64  # VRF Beacon smart contract commitment round value
    expiry_round: (
        arc4.UInt64
    )  # Round after registration expires and box can be deleted by others


# Define a struct that will store the game state object data
class GameState(arc4.Struct):
    staking_closed: arc4.Bool  # If True, game is live, else players can join
    # quick_play_enabled: arc4.Bool  # If True, admin can start live phase
    lobby_size: arc4.UInt8  #  Maximum num of player that can join the lobby
    active_players: arc4.UInt8  # Active num of players currently in lobby
    box_l_start_pos: (
        arc4.UInt16
    )  # Index where next address byte array is added to the game lobby box
    expiry_ts: arc4.UInt64  # Expiry timestamp of game phase, queue or live
    prize_pot: arc4.UInt64  # Prize pot amount for winner payouts
    admin_address: arc4.Address  # Game creator address, assigned as admin


# Define a struct that will store the game character object data
class GameCharacter(arc4.Struct):
    id: arc4.UInt8
    current_pos: arc4.UInt8
    new_pos: arc4.UInt8
    move_points: arc4.UInt8
    direction: arc4.UInt8
    # health: arc4.UInt8
    # action: arc4.UInt8
    # range: arc4.UInt8
    # accuracy: arc4.UInt8
