from typing import List, Optional, Sequence, Set, Tuple

from quarto_lib.contracts.models import Board, GameState
from quarto_lib.types.cell import Cell
from quarto_lib.types.piece import Piece


def get_available_pieces(game: GameState) -> Set[Piece]:
    pieces = set(Piece)
    pieces.discard(game.current_piece)
    for row in game.board:
        for piece in row:
            if piece is not None:
                pieces.discard(piece)

    return pieces


def get_available_cells(game: GameState) -> Set[Cell]:
    available_cells = set([cell for cell in Cell if game.board[cell.row][cell.col] is None])
    return available_cells


def common_characteristics(line: Sequence[Optional[Piece]]) -> List[Tuple[int, int]]:
    results: list[Tuple[int, int]] = []
    parsed_line = [piece for piece in line if piece is not None]
    if not parsed_line:
        return results
    for bit_index in range(4):
        bits = [(v.value >> bit_index) & 1 for v in parsed_line]
        if all(b == bits[0] for b in bits):
            results.append((bit_index, bits[0]))
    return results


def get_all_lines(board: Board) -> List[List[Optional[Piece]]]:
    lines: List[List[Optional[Piece]]] = []

    for i in range(4):
        lines.append([board[i][j] for j in range(4)])
        lines.append([board[j][i] for j in range(4)])

    lines.append([board[i][i] for i in range(4)])
    lines.append([board[i][3 - i] for i in range(4)])

    return lines


def check_win(board: Board) -> bool:
    for line in get_all_lines(board):
        line_pieces = [piece for piece in line if piece is not None]
        if len(line_pieces) == 4 and common_characteristics(line_pieces):
            return True

    return False


def piece_to_parts(piece: Piece) -> Tuple[str, str, bool, str, str]:
    color = (piece.value >> 0) & 1
    shape = (piece.value >> 1) & 1
    height = (piece.value >> 2) & 1
    fill = (piece.value >> 3) & 1

    char = ""
    if shape == 0:
        char = "●" if fill == 0 else "○"
    else:
        char = "■" if fill == 0 else "□"
    prefix, suffix = ("⌈", "⌉") if height else (" ", " ")
    template = "{prefix}{char}{suffix}"
    return char, template, bool(color), prefix, suffix
