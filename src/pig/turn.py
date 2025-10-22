"""Turn logic for the Pig game."""
from __future__ import annotations
from pig.dice import Dice
from pig.player import Player


class Turn:
    """
    Handles one player's turn in the Pig game.

    Keeps track of rolls, points earned this turn,
    and whether the turn has ended.
    """

    def __init__(self, player: Player, dice: Dice | None = None) -> None:
        self.player = player
        self.dice = dice or Dice()
        self.points = 0
        self.finished = False
        self.busted = False

    def roll(self) -> int:
        """
        Roll the dice once.
        If it's a 1, the turn ends and all points are lost.
        Otherwise, the roll value is added to this turn's total.
        """
        if self.finished:
            return 0  # can't roll after the turn is done

        value = self.dice.roll()
        if value == 1:
            self.points = 0
            self.finished = True
            self.busted = True
        else:
            self.points += value
        return value

    def hold(self) -> None:
        """
        End the turn and add the turn points to the player's score.
        Does nothing if the turn has already ended.
        """
        if self.finished:
            return
        self.player.add_score(self.points)
        self.finished = True

    def reset(self) -> None:
        """Reset the turn so it can be reused."""
        self.points = 0
        self.finished = False
        self.busted = False

    def __str__(self) -> str:
        """Quick string view for printing or debugging."""
        state = "busted" if self.busted else "active" if not self.finished else "done"
        return f"Turn({self.player.name}: {self.points} pts, {state})"
