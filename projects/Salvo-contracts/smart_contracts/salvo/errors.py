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
INVALID_GRID_INDEX: Final[str] = (
    "Grid array index you are trying to access is out of range."
)
INVALID_GRID_COORDS: Final[str] = (
    "Grid array coords you are trying to access are out of bounds."
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
UPDATABLE_NOT_TRUE: Final[str] = (
    "Template variable 'UPDATABLE' needs to be 'True' at deploy-time."
)
# DELETEABLE_NOT_TRUE: Final[str] = "Template variable 'DELETABLE' needs to be 'True' at deploy-time."
