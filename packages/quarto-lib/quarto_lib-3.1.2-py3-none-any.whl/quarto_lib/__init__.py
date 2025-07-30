from importlib.metadata import PackageNotFoundError, version

from quarto_lib.arena import Arena
from quarto_lib.contracts.models import Board, ChooseInitialPieceResponse, CompleteTurnResponse, GameState
from quarto_lib.contracts.quarto_agents import QuartoAgent
from quarto_lib.game import Game
from quarto_lib.tournament_round import TournamentRound
from quarto_lib.types.cell import Cell
from quarto_lib.types.piece import Piece
from quarto_lib.types.turn import Turn
from quarto_lib.utils import (
    check_win,
    common_characteristics,
    get_all_lines,
    get_available_cells,
    get_available_pieces,
    piece_to_parts,
)

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = [
    "Arena",
    "Game",
    "TournamentRound",
    "Board",
    "Cell",
    "Piece",
    "Turn",
    "check_win",
    "common_characteristics",
    "get_all_lines",
    "piece_to_parts",
    "get_available_pieces",
    "get_available_cells",
    "GameState",
    "CompleteTurnResponse",
    "ChooseInitialPieceResponse",
    "QuartoAgent",
]
