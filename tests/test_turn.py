# tests/test_turn.py
import pytest
from pig.turn import Turn
from pig.player import Player
from pig.dice import Dice


def test_roll_accumulates_points_on_non_one():
    p = Player("Alice")

    class StubDice:
        seq = [3, 5]
        def roll(self): return self.seq.pop(0)

    t = Turn(p, StubDice())
    assert t.roll() == 3
    assert t.points == 3
    assert t.roll() == 5
    assert t.points == 8
    assert not t.finished
    assert not t.busted


def test_roll_of_one_busts_and_finishes_turn():
    p = Player("Bob")

    class StubDice:
        def roll(self): return 1

    t = Turn(p, StubDice())
    assert t.roll() == 1
    assert t.points == 0
    assert t.finished is True
    assert t.busted is True


def test_cannot_roll_after_finished_returns_zero_and_no_change():
    p = Player("Cara")

    class StubDice:
        seq = [2, 1]  # accumulate, then bust
        def roll(self): return self.seq.pop(0)

    t = Turn(p, StubDice())
    assert t.roll() == 2
    assert t.roll() == 1  # busts -> finished
    before = (t.points, t.finished, t.busted)
    assert t.roll() == 0  # ignored
    assert (t.points, t.finished, t.busted) == before


def test_hold_banks_points_and_finishes_turn():
    p = Player("Dan")

    class StubDice:
        def roll(self): return 4

    t = Turn(p, StubDice())
    t.roll(); t.roll()      # 8 points
    t.hold()
    assert p.score == 8
    assert t.finished is True
    assert t.busted is False
    # points remain stored on the turn object (useful for UI/debug)
    assert t.points == 8


def test_second_hold_does_nothing_when_already_finished():
    p = Player("Eve")

    class StubDice:
        def roll(self): return 6

    t = Turn(p, StubDice())
    t.roll(); t.roll()   # 12
    t.hold()
    assert p.score == 12
    t.hold()  # should be ignored
    assert p.score == 12


def test_roll_after_hold_is_ignored():
    p = Player("Finn")

    class StubDice:
        def roll(self): return 5

    t = Turn(p, StubDice())
    t.roll()
    t.hold()
    assert t.finished is True
    assert t.roll() == 0  # finished turns can't roll


def test_reset_clears_points_and_flags():
    p = Player("Gail")

    class StubDice:
        seq = [5, 1]
        def roll(self): return self.seq.pop(0)

    t = Turn(p, StubDice())
    t.roll()          # +5
    t.roll()          # bust -> finished
    assert t.finished and t.busted and t.points == 0

    t.reset()
    assert t.points == 0
    assert t.finished is False
    assert t.busted is False

    # after reset, we can roll again
    class StubDice2:
        def roll(self): return 3
    t.dice = StubDice2()
    assert t.roll() == 3
    assert t.points == 3


def test_uses_injected_dice_instance():
    p = Player("Hal")

    class CountingDice:
        def __init__(self): self.calls = 0
        def roll(self):
            self.calls += 1
            return 2

    d = CountingDice()
    t = Turn(p, d)
    t.roll(); t.roll(); t.roll()
    assert d.calls == 3
    assert t.points == 6


def test_str_shows_player_points_and_state_changes():
    p = Player("Ivy")

    class StubDice:
        def roll(self): return 1

    t = Turn(p, StubDice())
    s = str(t)
    assert p.name in s
    assert "0 pts" in s or "0" in s

    t.roll()  # bust
    s2 = str(t)
    assert "busted" in s2 or "done" in s2


def test_multiple_non_one_rolls_then_bust_resets_points_and_flags_correctly():
    p = Player("Jay")

    class StubDice:
        seq = [3, 4, 1]  # 7 then bust
        def roll(self): return self.seq.pop(0)

    t = Turn(p, StubDice())
    assert t.roll() == 3
    assert t.roll() == 4
    assert t.points == 7
    assert t.roll() == 1  # bust
    assert t.points == 0
    assert t.finished is True
    assert t.busted is True
