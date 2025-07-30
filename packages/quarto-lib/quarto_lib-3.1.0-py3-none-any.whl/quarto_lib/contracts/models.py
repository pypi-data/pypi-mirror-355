from typing import List, Optional

from pydantic import BaseModel

from quarto_lib.types.cell import Cell
from quarto_lib.types.piece import Piece


class GameState(BaseModel):
    board: "Board"
    current_piece: Piece


type Board = List[List[Optional[Piece]]]


class CompleteTurnResponse(BaseModel):
    piece: Optional[Piece] = None
    cell: Cell


class ChooseInitialPieceResponse(BaseModel):
    piece: Piece
