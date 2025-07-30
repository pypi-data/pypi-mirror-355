from abc import ABC, abstractmethod

from quarto_lib.contracts.models import ChooseInitialPieceResponse, CompleteTurnResponse, GameState


class QuartoAgent(ABC):
    @abstractmethod
    def choose_initial_piece(self) -> ChooseInitialPieceResponse:
        pass

    @abstractmethod
    def complete_turn(self, game: GameState) -> CompleteTurnResponse:
        pass
