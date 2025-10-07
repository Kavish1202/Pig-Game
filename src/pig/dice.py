"""Dice utilities for the Pig game."""
from __future__ import annotations
import random

class Dice:
    """A standard six-sided dice."""

    def __init__(self, sides: int = 6) -> None:
        """Create a dice with a given number of sides (default 6)."""
        if sides < 2:
            raise ValueError("Dice must have at least 2 sides.")
        self.sides = sides

    def roll(self) -> int:
        """Roll the dice and return a value between 1 and `sides`."""
        return random.randint(1, self.sides)