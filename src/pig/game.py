"""Core game loop logic for Pig."""
from __future__ import annotations
from dataclasses import dataclass, field
from pig.dice import Dice
from pig.player import Player


@dataclass
class Game:
    """Minimal, testable Pig game core."""
    target: int = 100
    dice: Dice = field(default_factory=Dice)
    players: list[Player] = field(default_factory=lambda: [Player("Player 1"), Player("Player 2")])
    current_index: int = 0
    turn_points: int = 0
    winner_id: str | None = None

    @property
    def current(self) -> Player:
        return self.players[self.current_index]

    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current_index]

    def roll(self) -> int:
        """Roll the dice; 1 = bust (lose turn points, switch). Otherwise accumulate."""
        if self.winner_id is not None:
            return 0  # game over — ignore further rolls
        value = self.dice.roll()
        if value == 1:
            self.turn_points = 0
            self._switch()
        else:
            self.turn_points += value
        return value

    def hold(self) -> None:
        """Bank turn points to current player, check win, then switch."""
        if self.winner_id is not None:
            return
        self.current.add_score(self.turn_points)
        self.turn_points = 0
        if self.current.score >= self.target:
            self.winner_id = self.current.player_id
            return
        self._switch()

    def reset(self, *, keep_names: bool = True) -> None:
        """Reset scores/turn while optionally keeping player names/ids."""
        names = [p.name for p in self.players] if keep_names else ["Player 1", "Player 2"]
        self.players = [Player(names[0]), Player(names[1])]
        self.current_index = 0
        self.turn_points = 0
        self.winner_id = None

    def _switch(self) -> None:
        self.current_index = 1 - self.current_index
