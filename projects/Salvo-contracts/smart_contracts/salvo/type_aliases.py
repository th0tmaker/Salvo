# smart_contracts/salvo/type_aliases.py
from typing import Literal, TypeAlias

from algopy import arc4

# 11x11 game grid represented as a 1D flattened static array of 121 cells
GameGrid: TypeAlias = arc4.StaticArray[arc4.UInt8, Literal[121]]

# Dynamic array of user addresses denoting the game lobby
GameLobby: TypeAlias = arc4.DynamicArray[arc4.Address]

# Tuple acting as a pair of UInt8 coordinates (x=row, y=col) denoting character position
CoordsPair: TypeAlias = arc4.Tuple[arc4.UInt8, arc4.UInt8]

# Dynamic array of CoordsPair denoting multiple positions on the grid
CoordsArray: TypeAlias = arc4.DynamicArray[CoordsPair]

# Dynamic array of neighboring cells (up, down, left, right) in a 4-connected grid
Neighbors: TypeAlias = arc4.StaticArray[CoordsPair, Literal[4]]

# Tuple w/ neighbors and an UInt8 count value denoting how many neighbor values are valid path cells
NeighborsWithCount: TypeAlias = tuple[Neighbors, arc4.UInt8]
