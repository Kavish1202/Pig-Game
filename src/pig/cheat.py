# pig/cheat.py
"""Dev-only cheats. Keep this off in production."""

from __future__ import annotations
import os
from typing import Callable, Optional
from pig.game import Game


def cheats_enabled() -> bool:
    # Turn on by setting PIG_DEV=1 (or "true")
    return os.getenv("PIG_DEV", "0").lower() in {"1", "true", "yes"}


class Cheat:
    """
    Small helper that can rig dice and tweak scores.
    Only active if cheats_enabled() is True.
    """

    def __init__(self, game: Game) -> None:
        self.game = game
        self.active = cheats_enabled()
        self._orig_roll = game.dice.roll
        self._queue: list[int] = []          # forced next rolls
        self._no_bust: bool = False          # turn 1s into 2s (simple “no bust”)
        self._bias: Optional[Callable[[], int]] = None  # callable returning a 1..6

        if self.active:
            self._install_hook()

    # ---- public knobs ----

    def force_next_roll(self, value: int) -> None:
        if not self.active: return
        v = max(1, min(6, int(value)))
        self._queue.append(v)

    def force_next_rolls(self, *values: int) -> None:
        for v in values:
            self.force_next_roll(v)

    def no_bust_on_ones(self, on: bool = True) -> None:
        if not self.active: return
        self._no_bust = bool(on)

    def bias(self, chooser: Callable[[], int]) -> None:
        """Set a function that returns a biased roll (1..6)."""
        if not self.active: return
        self._bias = chooser

    def clear(self) -> None:
        if not self.active: return
        self._queue.clear()
        self._no_bust = False
        self._bias = None

    def add_points(self, player_no: int, pts: int) -> None:
        if not self.active: return
        self.game.players[player_no - 1].add_score(int(pts))

    def set_score(self, player_no: int, score: int) -> None:
        if not self.active: return
        p = self.game.players[player_no - 1]
        p.score = max(0, int(score))

    def win_now(self, player_no: int = 1) -> None:
        if not self.active: return
        me = self.game.players[player_no - 1]
        p = max(0, int(self.game.target))
        me.score = p
        self.game.winner_id = me.player_id

    # ---- hook machinery ----

    def _install_hook(self) -> None:
        orig = self._orig_roll

        def rigged_roll() -> int:
            # 1) forced values first
            if self._queue:
                return self._queue.pop(0)

            # 2) biased chooser, if any
            if self._bias is not None:
                v = int(self._bias())
                v = max(1, min(6, v))
                return 2 if (self._no_bust and v == 1) else v

            # 3) original dice, with optional “no bust”
            v = orig()
            if self._no_bust and v == 1:
                return 2
            return v

        # replace the dice's roll with our wrapper
        setattr(self.game.dice, "roll", rigged_roll)

    def uninstall(self) -> None:
        if not self.active: return
        setattr(self.game.dice, "roll", self._orig_roll)
        self.clear()

    def arm(self) -> None:
        """Turn cheats on right now (ignores env)."""
        if self.active:
            return
        self.active = True
        self._install_hook()