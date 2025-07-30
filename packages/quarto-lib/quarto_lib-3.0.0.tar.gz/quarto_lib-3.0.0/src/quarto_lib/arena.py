import logging
from typing import Optional, Tuple

from quarto_lib.contracts.models import GameState
from quarto_lib.contracts.quarto_agents import QuartoAgent
from quarto_lib.game import Game
from quarto_lib.types.cell import Cell

logger = logging.getLogger(__name__)


class Arena:
    def __init__(self, agent1: QuartoAgent, agent2: QuartoAgent):
        self.agent1 = agent1
        self.agent2 = agent2
        self.game: Game

    def play(self) -> Tuple[Optional[int], list[list[Cell]]]:
        self.game = Game()
        while not self.game.is_game_over:
            if self.game.is_fresh:
                if self.game.current_player == 0:
                    response = self.agent1.choose_initial_piece()
                else:
                    response = self.agent2.choose_initial_piece()
                self.game.choose_piece(response.piece)
                continue

            # Finish the game if there is only one option left
            if len(self.game.available_cells) == 1:
                cell = self.game.available_cells[0]
                self.game.place_piece(cell)
                continue

            # If not fresh, proceed with the turn
            if self.game.current_player == 0:
                response = self.agent1.complete_turn(GameState.from_game(self.game))
            else:
                response = self.agent2.complete_turn(GameState.from_game(self.game))

            logger.debug(f"Player {self.game.current_player} placed piece {response.piece} at cell {response.cell}")
            self.game.place_piece(response.cell)
            if self.game.is_game_over:
                break
            if response.piece is None:
                raise ValueError("Agent returned None for piece, which is not allowed at this stage of the game.")
            self.game.choose_piece(response.piece)

        return self.game.winner, self.game.winning_lines
