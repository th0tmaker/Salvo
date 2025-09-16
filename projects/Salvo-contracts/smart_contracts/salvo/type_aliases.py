# smart_contracts/salvo/type_aliases.py
from typing import Literal, TypeAlias

from algopy import arc4

# Define a 11x11 grid as an ARC-4 Static Array data type w/ 121 bytes in size
GameGrid: TypeAlias = arc4.StaticArray[arc4.UInt8, Literal[121]]

# Define the game lobby as an ARC-4 Dynamic Array data type w/ ARC-4 Address as the value data type
GameLobby: TypeAlias = arc4.DynamicArray[arc4.Address]

# Define the game grid x and y coordinates as UInt8 values inside an ARC-4 Tuple
GridCoords: TypeAlias = arc4.Tuple[arc4.UInt8, arc4.UInt8]

MoveSequence: TypeAlias = arc4.DynamicArray[GridCoords]
