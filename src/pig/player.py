"""Player class for the Pig game."""
from __future__ import annotations
from uuid import uuid4


class Player:
    """
    Represents one player in the Pig game.

    Each player has a unique ID that stays the same even if their name changes.
    """

    def __init__(self, name: str = "Player") -> None:
        name = self._clean_name(name)
        if not name:
            raise ValueError("Player name can't be empty.")
        self.player_id: str = uuid4().hex
        self.name: str = name
        self.score: int = 0

    @staticmethod
    def _clean_name(value: str | None) -> str:
        """Make sure the name is a string and has no extra spaces."""
        if value is None:
            return ""
        return str(value).strip()

    def change_name(self, new_name: str) -> None:
        """Update the player's name but keep the same ID."""
        new_name = self._clean_name(new_name)
        if not new_name:
            raise ValueError("Player name can't be empty.")
        self.name = new_name

    def add_score(self, points: int) -> None:
        """Add points to the player's score."""
        if not isinstance(points, int):
            raise TypeError("points must be an integer")
        if points < 0:
            raise ValueError("points can't be negative")
        self.score += points

    def reset_score(self) -> None:
        """Set the player's score back to zero."""
        self.score = 0

    def __str__(self) -> str:
        """Simple text form for printing to console."""
        return f"{self.name} - {self.score} pts"

    def to_dict(self) -> dict[str, str | int]:
        """Return player data as a plain dictionary."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "score": self.score,
        }   
