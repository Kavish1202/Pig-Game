# tests/test_cheat.py
# tests for pig/cheat.py
# goal: hit every single branch with natural, readable tests

import pytest
from pig.game import Game
from pig.cheat import Cheat, cheats_enabled


# a simple dice we can control (no randomness)
class TweakDice:
    def __init__(self, v=3):
        self.v = v
    def roll(self):
        return self.v


# 1) env flag variations
def test_cheats_enabled_env_variants(monkeypatch):
    # default: off
    monkeypatch.delenv("PIG_DEV", raising=False)
    assert cheats_enabled() is False

    # true-ish values should turn it on
    for val in ["1", "true", "True", "YES", "yes"]:
        monkeypatch.setenv("PIG_DEV", val)
        assert cheats_enabled() is True

    # zero turns it off again
    monkeypatch.setenv("PIG_DEV", "0")
    assert cheats_enabled() is False


# 2) inactive cheat = should do nothing at all
def test_inactive_cheat_noop(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=4)
    orig_fn = g.dice.roll

    c = Cheat(g)
    assert c.active is False  # should be inactive

    # all these calls should silently do nothing
    c.force_next_roll(6)
    c.force_next_rolls(2, 3)
    c.no_bust_on_ones(True)
    c.bias(lambda: 6)
    c.clear()
    c.add_points(1, 50)
    c.set_score(2, 99)
    # win_now returns None in your version; just verify state didn't change
    c.win_now(1)
    assert g.winner_id is None
    assert g.players[0].score == 0
    assert g.players[1].score == 0

    c.uninstall()  # no-op
    assert getattr(g.dice.roll, "__func__", None) is getattr(orig_fn, "__func__", None)
    assert g.dice.roll() == 4


# 3) arm() activates and queue overrides all rolls
def test_arm_hook_and_queue_priority(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=3)

    c = Cheat(g)
    c.arm()
    assert c.active

    # queue values should come out exactly like we give them (and clamp properly)
    c.force_next_rolls(6, 1, 2, 99, 0)
    assert g.dice.roll() == 6
    assert g.dice.roll() == 1
    assert g.dice.roll() == 2
    assert g.dice.roll() == 6  # 99 clamped
    assert g.dice.roll() == 1  # 0 clamped
    # after queue is empty, go back to original dice value
    assert g.dice.roll() == 3


# 4) no-bust mode only applies when reading actual dice or bias, not queued rolls
def test_no_bust_applies_to_nonqueue_only(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=1)
    c = Cheat(g)
    c.arm()

    c.no_bust_on_ones(True)
    c.force_next_roll(1)
    assert g.dice.roll() == 1  # queue stays 1

    # with empty queue, now no-bust turns 1 into 2
    assert g.dice.roll() == 2

    # back to normal once we turn it off
    c.no_bust_on_ones(False)
    assert g.dice.roll() == 1


# 5) bias function is used and clamped 1..6, interacts with no-bust
def test_bias_used_and_clamped_with_nobust(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=4)
    c = Cheat(g)
    c.arm()

    c.bias(lambda: 5)
    assert g.dice.roll() == 5  # bias wins

    c.bias(lambda: 0)
    assert g.dice.roll() == 1  # clamped up

    c.no_bust_on_ones(True)
    c.bias(lambda: 1)
    assert g.dice.roll() == 2  # 1 becomes 2 with no-bust

    c.bias(lambda: 99)
    assert g.dice.roll() == 6  # clamped down

    c.clear()
    assert g.dice.roll() == 4  # back to normal


# 6) add_points + set_score should work and clamp negatives
def test_add_points_and_set_score(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    c = Cheat(g)
    c.arm()

    c.add_points(1, 7)
    assert g.players[0].score == 7

    c.set_score(2, -5)  # negative becomes 0
    assert g.players[1].score == 0

    c.set_score(2, 42)
    assert g.players[1].score == 42


# 7) win_now should set winner_id and ensure score >= target
def test_win_now_sets_winner_and_score(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game(target=20)
    c = Cheat(g)
    c.arm()

    # don't rely on return; check state after call
    c.win_now(1)
    assert g.winner_id == g.players[0].player_id
    assert g.players[0].score >= g.target

    g.reset()
    c.win_now(2)
    assert g.winner_id == g.players[1].player_id
    assert g.players[1].score >= g.target



# 8) uninstall should restore the original dice roll
def test_uninstall_behavior(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=2)

    # inactive uninstall
    c1 = Cheat(g)
    c1.uninstall()
    assert g.dice.roll() == 2

    # active uninstall replaces rigged roll with original
    c2 = Cheat(g)
    c2.arm()
    rigged_fn = g.dice.roll
    c2.uninstall()
    assert g.dice.roll is not rigged_fn
    assert g.dice.roll() == 2


# 9) arm() should be safe to call twice, clear() should reset everything
def test_arm_idempotent_and_clear(monkeypatch):
    monkeypatch.delenv("PIG_DEV", raising=False)
    g = Game()
    g.dice = TweakDice(v=3)
    c = Cheat(g)

    c.arm()
    first_fn = g.dice.roll
    c.arm()  # should not wrap again
    second_fn = g.dice.roll
    assert first_fn is second_fn

    c.force_next_rolls(6, 6)
    c.no_bust_on_ones(True)
    c.bias(lambda: 5)
    c.clear()
    # now everything reset, dice back to normal
    assert g.dice.roll() == 3


# 10) env already set should make Cheat active immediately
def test_active_on_init_and_queue_beats_bias(monkeypatch):
    monkeypatch.setenv("PIG_DEV", "1")
    g = Game()
    g.dice = TweakDice(v=6)

    c = Cheat(g)
    assert c.active  # auto active due to env

    # if both queue + bias exist, queue values should come first
    c.bias(lambda: 1)
    c.force_next_rolls(4, 5)
    assert g.dice.roll() == 4
    assert g.dice.roll() == 5
    # once queue empty, bias takes over
    assert g.dice.roll() == 1