# smart_contracts/salvo/type_aliases.py
from typing import Literal, NamedTuple, TypeAlias

from algopy import UInt64, arc4

# Define a 11x11 grid as an ARC-4 Static Array data type w/ 121 bytes in size
GameGrid: TypeAlias = arc4.StaticArray[arc4.UInt8, Literal[121]]

# Define a game lobby as an ARC-4 Dynamic Array data type w/ ARC-4 Address as the value data type
GameLobby: TypeAlias = arc4.DynamicArray[arc4.Address]


# Define a named tuple for the game grid x and y coordinates
class GridCoords(NamedTuple):
    x: UInt64
    y: UInt64
