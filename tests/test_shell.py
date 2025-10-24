import json
import types
import pytest
import builtins

from pig.game import Game
from pig.turn import Turn
from pig.player import Player
from pig.scoreboard import Scoreboard
import pig.shell as shell


# Helper Classes and Functions
class OneDice:
    """Dice that always rolls 1."""

    def roll(self):
        return 1


class ConstDice:
    """Dice that rolls a constant value."""

    def __init__(self, v):
        self.v = v

    def roll(self):
        return self.v


class SeqDice:
    """Dice that rolls values from a predefined sequence."""

    def __init__(self, seq):
        """Init."""
        self.seq = list(seq)

    def roll(self):
        """Roll."""
        return self.seq.pop(0)


def set_save_path(tmp_path, monkeypatch):
    """Set the scoreboard save path for testing."""
    p = tmp_path / "scoreboard.json"
    monkeypatch.setattr(shell, "SAVE_PATH", p, raising=True)
    return p


# Tests
def test_startup_prompts_pvc_and_sets_brain_and_name(monkeypatch, capsys):
    """Test PvC mode setup with difficulty and computer name."""
    inputs = iter(["2", "3"])  # PvC, Hard
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()

    assert sh.mode == "pvc"
    assert sh.difficulty == "hard"
    assert sh.brain is not None
    assert sh.game.players[1].name == "Computer"
    out = capsys.readouterr().out
    assert "Mode set to pvc (hard)" in out
    assert "Pig — first to" in out
    assert "Current:" in out


def test_startup_prompts_pvp(monkeypatch, capsys):
    """Test PvP mode setup."""
    inputs = iter(["1"])  # PvP
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()
    assert sh.mode == "pvp"
    assert sh.brain is None
    out = capsys.readouterr().out
    assert "Mode set to pvp" in out


def test_do_status_prints_header(capsys):
    """Test status command prints game header."""
    sh = shell.PigShell(Game(), Scoreboard())
    sh._print_header()
    sh.do_status("")
    out = capsys.readouterr().out
    assert "Pig — first to" in out
    assert "Current:" in out


def test_do_roll_normal_and_bust_outputs(capsys):
    """Test roll command outputs for normal roll and bust."""
    g = Game()
    g.dice = SeqDice([4, 1])
    g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    sh.do_roll("")
    out1 = capsys.readouterr().out
    assert "Rolled 4" in out1
    assert "Turn points: 4" in out1

    sh.do_roll("")
    out2 = capsys.readouterr().out
    assert "Rolled 1. BUST." in out2
    assert "Score this round: 0 points." in out2
    assert "Total score:" in out2
    assert "turn." in out2


def test_do_hold_banks_and_reports(capsys):
    """Test hold command banks points and reports status."""
    g = Game()
    g.dice = ConstDice(5)
    g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    sh.do_roll("")
    sh.do_roll("")  # 10 points
    sh.do_hold("")
    out = capsys.readouterr().out
    assert "Holding." in out
    assert "Current Score:" in out
    assert "turn." in out


def test_do_name_success_and_bad_usage(capsys):
    """Test name command sets player name and handles invalid input."""
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_name("1 Alice")
    assert sh.game.players[0].name == "Alice"
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1

    sh.do_name("oops")
    out2 = capsys.readouterr().out
    assert "Usage: name 1 Alice" in out2


def test_do_target_success_and_error(capsys):
    """Test target command sets target and handles invalid input."""
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_target("150")
    out1 = capsys.readouterr().out
    assert "Target set to 150" in out1
    assert sh.game.target == 150

    sh.do_target("zero")
    out2 = capsys.readouterr().out
    assert "Could not set target:" in out2


def test_do_reset_keep_and_clear(capsys):
    """Test reset command with keep and clear options."""
    g = Game()
    g.players[0].change_name("Alice")
    g.players[1].change_name("Bob")
    sh = shell.PigShell(g, Scoreboard())

    g.dice = ConstDice(6)
    g.turn.dice = g.dice
    sh.do_roll("")
    sh.do_hold("")
    assert g.players[0].score == 6

    sh.do_reset("keep")
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1
    assert [p.name for p in g.players] == ["Alice", "Bob"]
    assert g.players[0].score == 0

    sh.do_reset("clear")
    out2 = capsys.readouterr().out
    assert [p.name for p in g.players] == ["Player 1", "Player 2"]


def test_view_prints_recent_results(capsys):
    """Test view command prints recent scoreboard results."""
    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(12)
    b.add_score(7)
    sb.record(winner=a, players=[a, b], target=10)

    sh = shell.PigShell(Game(), sb)
    sh.do_view("")
    out = cap