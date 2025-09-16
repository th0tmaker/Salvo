# smart_contracts/salvo/type_aliases.py
from typing import Literal, TypeAlias

from algopy import arc4

# 11x11 game grid represented as a 1D flattened static array of 121 cells
GameGrid: TypeAlias = arc4.StaticArray[arc4.UInt8, Literal[121]]

# Dynamic array of user addresses representing the game lobby
GameLobby: TypeAlias = arc4.DynamicArray[arc4.Address]

# Grid cell coordinates as a tuple of (x=row, y=col), each as UInt8
GridCoords: TypeAlias = arc4.Tuple[arc4.UInt8, arc4.UInt8]

# Ordered dynamic array of grid coordinates representing a sequence of moves
MoveSequence: TypeAlias = arc4.DynamicArray[GridCoords]

# Dynamic array of valid neighboring cells (up, down, left, right) in a 4-connected grid
Neighbors: TypeAlias = arc4.StaticArray[GridCoords, Literal[4]]

# Tuple w/ neighbors and an UInt8 counter of valid neighbors
NeighborsValid: TypeAlias = tuple[Neighbors, arc4.UInt8]
