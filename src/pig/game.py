"""Core game loop logic for Pig."""
from __future__ import annotations
from dataclasses import dataclass, field
from pig.dice import Dice
from pig.player import Player
from pig.turn import Turn


@dataclass
class Game:
    """Minimal, testable Pig game core."""
    target: int = 100
    dice: Dice = field(default_factory=Dice)
    players: list[Player] = field(default_factory=lambda: [Player("Player 1"), Player("Player 2")])
    current_index: int = 0
    turn_points: int = 0
    winner_id: str | None = None

    def __post_init__(self) -> None:
        """Set up the first turn for Player 1."""
        self.turn = Turn(self.current, self.dice)

    @property
    def current(self) -> Player:
        return self.players[self.current_index]

    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current_index]
    
    def roll(self) -> int:
        """Roll the dice for the current player's turn."""
        if self.winner_id is not None:
            return 0  # game already over

        value = self.turn.roll()

        if self.turn.finished and self.turn.busted:
            # Player rolled a 1, loses points and switches turn
            self.turn_points = 0
            self._switch()
            self.turn = Turn(self.current, self.dice)
        else:
            self.turn_points = self.turn.points

        return value

    def hold(self) -> None:
        """End the turn, add points to score, and check for a winner."""
        if self.winner_id is not None:
            return

        self.turn.hold()
        self.turn_points = 0

        if self.current.score >= self.target:
            self.winner_id = self.current.player_id
            return

        self._switch()
        self.turn = Turn(self.current, self.dice)


    def reset(self, *, keep_names: bool = True) -> None:
        """Reset scores/turn while optionally keeping player names/ids."""
        names = [p.name for p in self.players] if keep_names else ["Player 1", "Player 2"]
        self.players = [Player(names[0]), Player(names[1])]
        self.current_index = 0
        self.turn_points = 0
        self.winner_id = None
        self.turn = Turn(self.current, self.dice)


    def _switch(self) -> None:
        self.current_index = 1 - self.current_index


    turn: Turn | None = field(default=None, init=False)

