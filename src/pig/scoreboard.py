# pig/scoreboard.py
"""Scoreboard for tracking Pig game results."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from pig.player import Player
from pig.game import Game


@dataclass
class ScoreRow:
    when: str              # Time when the game finished
    target: int            # Target score for that game
    winner: str            # Name of the winner
    scores: dict[str, int] # Final scores for all players


class Scoreboard:
    """Keeps a simple history of completed games."""

    def __init__(self) -> None:
        self.history: list[ScoreRow] = []

    def record_from_game(self, game: Game) -> None:
        """
        Save a finished game's result.
        Won't do anything if the game isn't over yet.
        """
        if game.winner_id is None:
            raise ValueError("Game isn't finished yet.")
        winner = self._get_winner(game.players, game.winner_id)
        row = ScoreRow(
            when=datetime.now().isoformat(timespec="seconds"),
            target=game.target,
            winner=winner.name,
            scores={p.name: p.score for p in game.players},
        )
        self.history.append(row)

    def record(self, *, winner: Player, players: Iterable[Player], target: int) -> None:
        """Manual way to add a result (if you’re not using a Game object)."""
        row = ScoreRow(
            when=datetime.now().isoformat(timespec="seconds"),
            target=target,
            winner=winner.name,
            scores={p.name: p.score for p in players},
        )
        self.history.append(row)

    def last(self, n: int = 5) -> list[ScoreRow]:
        """Return the most recent few games."""
        return self.history[-n:]

    def wins_table(self) -> dict[str, int]:
        """Count how many wins each player has."""
        wins: dict[str, int] = {}
        for row in self.history:
            wins[row.winner] = wins.get(row.winner, 0) + 1
        return wins

    def top(self, n: int = 3) -> list[tuple[str, int]]:
        """Return the top N players by total wins."""
        table = self.wins_table()
        return sorted(table.items(), key=lambda kv: (-kv[1], kv[0]))[:n]

    def reset(self) -> None:
        """Clear everything on the board."""
        self.history.clear()

    def to_dict(self) -> dict:
        """Convert the scoreboard into a plain dictionary (for saving)."""
        return {"history": [row.__dict__ for row in self.history]}

    @classmethod
    def from_dict(cls, data: dict) -> "Scoreboard":
        """Recreate a scoreboard from a saved dictionary."""
        sb = cls()
        for r in data.get("history", []):
            sb.history.append(ScoreRow(**r))
        return sb

    @staticmethod
    def _get_winner(players: Iterable[Player], winner_id: str) -> Player:
        """Find the player that matches the winner_id."""
        for p in players:
            if p.player_id == winner_id:
                return p
        raise ValueError("Winner not found in player list.")
