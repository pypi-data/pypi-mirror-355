from abc import ABC, abstractmethod

from quarto_lib.contracts.models import ChooseInitialPieceResponse, CompleteTurnResponse, GameState


class QuartoAgent(ABC):
    def __init__(self, identifier: str = "unknown-quarto-agent"):
        self._identifier = identifier

    @property
    def identifier(self) -> str:
        return self._identifier

    @abstractmethod
    def choose_initial_piece(self) -> ChooseInitialPieceResponse:
        pass

    @abstractmethod
    def complete_turn(self, game: GameState) -> CompleteTurnResponse:
        pass
