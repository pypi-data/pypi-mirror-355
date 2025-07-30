from typing import List, Optional

from pydantic import BaseModel

from quarto_lib.types.cell import Cell
from quarto_lib.types.piece import Piece


class GameState(BaseModel):
    board: List[List[Optional[Piece]]]
    current_piece: Piece


class CompleteTurnResponse(BaseModel):
    piece: Optional[Piece] = None
    cell: Cell


class ChooseInitialPieceResponse(BaseModel):
    piece: Piece
