# pig/ai.py
"""Computer strategies for Pig."""

from __future__ import annotations
from pig.game import Game


class ComputerStrategy:
    """Simple threshold bot. Easy mode."""

    def __init__(self, base_threshold: int = 20) -> None:
        self.base_threshold = base_threshold

    def decide(self, game: Game) -> str:
        me = game.current
        opp = game.opponent
        t = game.turn_points
        target = game.target

        if me.score + t >= target:
            return "hold"

        threshold = self.base_threshold
        gap = opp.score - me.score  # positive -> we're behind

        if gap >= 25:
            threshold += 10
        elif gap >= 10:
            threshold += 5
        elif gap <= -20:
            threshold -= 4

        return "hold" if t >= threshold else "roll"


class SmartStrategy:
    """Stronger bot. Adjusts to game state and endgame."""

    def __init__(self, min_threshold: int = 12, max_threshold: int = 28) -> None:
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def decide(self, game: Game) -> str:
        me = game.current
        opp = game.opponent
        t = game.turn_points
        target = game.target

        # never hold with zero banked
        if t == 0:
            return "roll"

        # win if we can
        if me.score + t >= target:
            return "hold"

        points_needed = max(0, target - me.score)
        opp_needed = max(0, target - opp.score)
        gap = opp.score - me.score  # positive -> we're behind

        # tight endgame: only hold if this actually finishes the game
        if points_needed <= 8:
            if t >= points_needed:       # must be enough to win now
                return "hold"
            return "roll"

        # base threshold scales with distance to target
        threshold = (points_needed // 2) + 8
        threshold = max(self.min_threshold, min(self.max_threshold, threshold))

        # adjust for score gap
        if gap >= 20:
            threshold += 6
        elif gap >= 10:
            threshold += 3
        elif gap <= -20:
            threshold -= 4
        elif gap <= -10:
            threshold -= 2

        # if opponent is close to winning, push harder
        if opp_needed <= 15:
            threshold = max(threshold, 22)

        return "hold" if t >= threshold else "roll"