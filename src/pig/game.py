"""Core game loop logic for Pig."""
from __future__ import annotations
from dataclasses import dataclass, field
from pig.dice import Dice
from pig.player import Player
from pig.turn import Turn


@dataclass
class Game:
    """Plain game state + rules. No printing, no input — just logic."""

    target: int = 100
    dice: Dice = field(default_factory=Dice)
    players: list[Player] = field(
        default_factory=lambda: [Player("Player 1"), Player("Player 2")]
    )
    current_index: int = 0
    turn_points: int = 0
    winner_id: str | None = None
    # not passed in by callers; created on init/reset/switch
    turn: Turn | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize transient turn state after dataclass init.

        Start with Player 1.
        """
        # start with Player 1
        self.turn = Turn(self.current, self.dice)

    # --- convenience bits the UI can use ---

    @property
    def current(self) -> Player:
        """Return the current player in the game."""
        return self.players[self.current_index]

    @property
    def opponent(self) -> Player:
        """Return the opposing player in the game."""
        return self.players[1 - self.current_index]

    @property
    def is_over(self) -> bool:
        """Return True if the game has a winner (i.e., the game is over)."""
        return self.winner_id is not None

    def get_winner(self) -> Player | None:
        """Return the winning Player object if there is a winner.

        Returns None if the game is not over.
        """
        if self.winner_id is None:
            return None
        for p in self.players:
            if p.player_id == self.winner_id:
                return p
        return None

    def set_target(self, new_target: int) -> None:
        """Set a new target score for the game.

        Args:
            new_target (int): The new target score to set. Must be a
                positive integer.

        Raises:
            TypeError: If new_target is not an integer.
            ValueError: If new_target is less than 1.
        """
        if not isinstance(new_target, int):
            raise TypeError("target must be an int")
        if new_target < 1:
            raise ValueError("target must be >= 1")
        self.target = new_target

    def rename(self, player_no: int, new_name: str) -> None:
        """Rename a player in the game.

        Args:
            player_no (int): The player number (1 or 2) to rename.
            new_name (str): The new name for the player.

        Raises:
            ValueError: If player_no is not 1 or 2.
        """
        # CLI uses 1/2, so accept that here
        if player_no not in (1, 2):
            raise ValueError("player_no must be 1 or 2")
        self.players[player_no - 1].change_name(new_name)

    def snapshot(self) -> dict:
        """Small dict the UI can print or log."""
        return {
            "target": self.target,
            "current": self.current.name,
            "turn_points": self.turn_points,
            "scores": {p.name: p.score for p in self.players},
            "winner": (self.get_winner().name if self.is_over else None),
        }

    # --- core rules ---

    def roll(self) -> int:
        """Roll for the current player. Handles bust + turn switch."""
        if self.winner_id is not None:
            return 0  # game is done

        value = self.turn.roll()

        if self.turn.finished and self.turn.busted:
            # rolled a 1 — lose turn points and switch
            self.turn_points = 0
            self._switch()
            self.turn = Turn(self.current, self.dice)
        else:
            self.turn_points = self.turn.points

        return value

    def hold(self) -> None:
        """Bank points for current player. Check win, otherwise switch."""
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
        """Reset scores/turn. Keep player names if asked."""
        if keep_names:
            names = [p.name for p in self.players]
        else:
            names = ["Player 1", "Player 2"]
        self.players = [Player(names[0]), Player(names[1])]
        self.current_index = 0
        self.turn_points = 0
        self.winner_id = None
        self.turn = Turn(self.current, self.dice)

    def _switch(self) -> None:
        self.current_index = 1 - self.current_index

    # --- CPU driver (UI-free): run a whole bot turn with a strategy ---

    def play_cpu_turn(self, decide) -> dict:
        """Run the computer's turn using a strategy function.

        The strategy function decide(game) returns either "roll" or "hold".
        Returns a summary dict the UI can print.
        """
        actions: list[dict] = []
        while True:
            choice = decide(self)
            if choice == "roll":
                value = self.roll()
                actions.append({"action": "roll", "value": value})
                if value == 1:
                    # busted; turn already switched during roll()
                    return {
                        "ended": "bust",
                        "actions": actions,
                        "current": self.current.name
                    }
            else:
                # hold — may win or switch
                player_name_before = self.current.name
                self.hold()
                actions.append({"action": "hold"})
                if self.is_over:
                    return {
                        "ended": "win",
                        "winner": player_name_before,
                        "actions": actions
                    }
                return {"ended": "hold", "next": self.current.name,
                        "actions": actions}