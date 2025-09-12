# smart_contracts/salvo/type_aliases.py
from typing import Literal, NamedTuple, TypeAlias

from algopy import UInt64, arc4

# Define an 11x11 grid as a static array of 121 bytes
GameGrid: TypeAlias = arc4.StaticArray[arc4.UInt8, Literal[121]]

# Type alias from arc4 dynamic array data type
GameLobby: TypeAlias = arc4.DynamicArray[arc4.Address]


# Define a tuple for the game grid x and y coordinates
class GridCoords(NamedTuple):
    x: UInt64
    y: UInt64
