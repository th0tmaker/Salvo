# smart_contracts/salvo/errors.py
from typing import Final

# Define assert error messages
UNAUTH_CREATOR: Final[str] = (
    "Sender address is not authorized to create this application."
)
SENDER_NOT_CREATOR: Final[str] = "Only app creator can act as the sender address."
INVALID_GROUP_SIZE: Final[str] = (
    "Invalid group size. Ensure number of transactions in group is within valid bounds."
)
INVALID_LOBBY_SIZE: Final[str] = (
    "Invalid Lobby size. Value must be an even number and within permitted bounds."
)
INVALID_POS_INDEX: Final[str] = (
    "Invalid position index. Ensure index value is within valid range."
)
INVALID_POS_COORDS: Final[str] = (
    "Invalid position coordinates. Ensure boh row and column indices are within valid range."
)
INVALID_MOVE_SEQUENCE: Final[str] = (
    "Invalid move sequence. Ensure coordinate entries within the movement array are valid path cells."
)
INVALID_STAKE_AMOUNT: Final[str] = (
    "Invalid stake amount. Value must be a multiple of 1 and within permitted bounds."
)
INSUFFICIENT_PAY_AMOUNT: Final[str] = (
    "Insufficient payment amount. Value is not enough to cover the minimum requirements."
)
INVALID_STAKE_PAY_SENDER: Final[str] = (
    "Stake payment sender address must match sender address."
)
INVALID_STAKE_PAY_RECEIVER: Final[str] = (
    "Stake payment receiver address must match application address."
)
INVALID_BOX_PAY_SENDER: Final[str] = (
    "Box payment sender address must match transaction sender address."
)
INVALID_BOX_PAY_RECEIVER: Final[str] = (
    "Box payment receiver address must match application address."
)
BOX_NOT_FOUND: Final[str] = (
    "Box not found. Ensure the box was created and still exists."
)
BOX_FOUND: Final[str] = "Box found. Ensure the does not exist already."
GAME_ID_NOT_FOUND: Final[str] = (
    "Game ID not found. Ensure the game was created and still exists."
)
POSITION_MISMATCH: Final[str] = (
    "Position mismatch. Position value must be equal to expected corresponding state value."
)
MOVEMENT_OVERFLOW: Final[str] = (
    "Movement overflow. Ensure movement length (num of indicies) is within valid range."
)
ACTION_OVERFLOW: Final[str] = (
    "Action overflow. Ensure action index is within valid range."
)
DIRECTION_OVERFLOW: Final[str] = (
    "Direction overflow. Ensure direction index is within valid range."
)
UPDATABLE_NOT_TRUE: Final[str] = (
    "Template variable 'UPDATABLE' needs to be 'True' at deploy-time."
)
# DELETEABLE_NOT_TRUE: Final[str] = "Template variable 'DELETABLE' needs to be 'True' at deploy-time."
