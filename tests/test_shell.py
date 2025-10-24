# tests/test_shell.py
import builtins
import json
import types
import pytest

from pig.game import Game
from pig.turn import Turn
from pig.player import Player
from pig.scoreboard import Scoreboard
import pig.shell as shell


# ---------- helpers ----------

class OneDice:
    def roll(self): return 1

class ConstDice:
    def __init__(self, v): self.v = v
    def roll(self): return self.v

class SeqDice:
    def __init__(self, seq): self.seq = list(seq)
    def roll(self): return self.seq.pop(0)

def set_save_path(tmp_path, monkeypatch):
    p = tmp_path / "scoreboard.json"
    monkeypatch.setattr(shell, "SAVE_PATH", p, raising=True)
    return p


# ---------- tests ----------

def test_startup_prompts_pvc_and_sets_brain_and_name(monkeypatch, capsys):
    # Feed: [2]=PvC, [3]=Hard
    inputs = iter(["2", "3"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()  # triggers prompt + header

    assert sh.mode == "pvc"
    assert sh.difficulty == "hard"
    assert sh.brain is not None
    # Player 2 renamed to Computer
    assert sh.game.players[1].name == "Computer"

    out = capsys.readouterr().out
    assert "Mode set to pvc (hard)" in out
    assert "Pig — first to" in out
    assert "Current:" in out


def test_startup_prompts_pvp(monkeypatch, capsys):
    inputs = iter(["1"])  # PvP; no difficulty prompt
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()
    assert sh.mode == "pvp"
    assert sh.brain is None
    out = capsys.readouterr().out
    assert "Mode set to pvp" in out


def test_do_status_prints_header(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    # Avoid prompting
    sh._print_header()
    sh.do_status("")
    out = capsys.readouterr().out
    assert "Pig — first to" in out
    assert "Current:" in out


def test_do_roll_normal_and_bust_outputs(capsys):
    g = Game()
    # First two rolls: 4 then 1 (bust)
    g.dice = SeqDice([4, 1]); g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    # no prompt; directly call command
    sh.do_roll("")
    out1 = capsys.readouterr().out
    assert "Rolled 4" in out1
    assert "Turn points: 4" in out1

    sh.do_roll("")
    out2 = capsys.readouterr().out
    assert "Rolled 1. BUST." in out2
    assert "Score this round: 0 points." in out2
    assert "Total score:" in out2
    assert "turn." in out2  # next player's turn line


def test_do_hold_banks_and_reports(capsys):
    g = Game()
    g.dice = ConstDice(5); g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    sh.do_roll(""); sh.do_roll("")  # 10
    sh.do_hold("")
    out = capsys.readouterr().out
    assert "Holding." in out
    # It prints opponent score after banking
    assert "Current Score:" in out
    # Should be next player's turn line
    assert "turn." in out


def test_do_name_success_and_bad_usage(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_name("1 Alice")
    assert sh.game.players[0].name == "Alice"
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1  # header reprinted

    sh.do_name("oops")
    out2 = capsys.readouterr().out
    assert "Usage: name 1 Alice" in out2


def test_do_target_success_and_error(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_target("150")
    out1 = capsys.readouterr().out
    assert "Target set to 150" in out1
    assert sh.game.target == 150

    sh.do_target("zero")
    out2 = capsys.readouterr().out
    assert "Could not set target:" in out2  # error path


def test_do_reset_keep_and_clear(capsys):
    g = Game()
    g.players[0].change_name("Alice")
    g.players[1].change_name("Bob")
    sh = shell.PigShell(g, Scoreboard())

    # Give Alice some points then reset keeping names
    g.dice = ConstDice(6); g.turn.dice = g.dice
    sh.do_roll(""); sh.do_hold("")
    assert g.players[0].score == 6

    sh.do_reset("keep")
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1
    assert [p.name for p in g.players] == ["Alice", "Bob"]
    assert g.players[0].score == 0 and g.players[1].score == 0

    # Clear names back to defaults
    sh.do_reset("clear")
    out2 = capsys.readouterr().out
    assert [p.name for p in g.players] == ["Player 1", "Player 2"]


def test_view_prints_recent_results(capsys):
    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(12); b.add_score(7)
    sb.record(winner=a, players=[a, b], target=10)

    sh = shell.PigShell(Game(), sb)
    sh.do_view("")
    out = capsys.readouterr().out
    assert "Recent results:" in out
    assert "winner: A" in out


def test_do_mode_and_do_diff_switching_and_brain(capsys):
    sh = shell.PigShell(Game(), Scoreboard())

    sh.do_mode("pvc")
    assert sh.mode == "pvc"
    # default difficulty "normal" -> brain is set
    assert sh.brain is not None
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1

    sh.do_diff("hard")
    assert sh.difficulty == "hard"
    assert sh.brain is not None
    out2 = capsys.readouterr().out
    assert "Difficulty set to hard." in out2

    sh.do_mode("pvp")
    assert sh.mode == "pvp"
    assert sh.brain is None


def test_invalid_mode_and_diff_messages(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_mode("xyz")
    out1 = capsys.readouterr().out
    assert "Pick 'pvp' or 'pvc'." in out1

    sh.do_diff("bananas")
    out2 = capsys.readouterr().out
    assert "Pick 'easy', 'normal' or 'hard'." in out2


def test_cpu_turn_roll_then_hold_flow(capsys):
    g = Game()
    # Switch to PvC mode manually
    sh = shell.PigShell(g, Scoreboard())
    sh.mode = "pvc"
    # brain: first decide roll, then hold
    class Brain:
        def __init__(self): self.n = 0
        def decide(self, game):
            self.n += 1
            return "roll" if self.n == 1 else "hold"
    sh.brain = Brain()

    # CPU (Player 2) to move
    g.current_index = 1
    g.turn = Turn(g.current, g.dice)

    g.dice = SeqDice([4])  # CPU rolls 4, then holds
    g.turn.dice = g.dice

    sh._cpu_take_turn()
    out = capsys.readouterr().out
    assert "CPU rolled 4" in out
    assert "CPU holds." in out
    # After hold it's Player 1's turn
    assert g.current is g.players[0]


def test_cpu_turn_bust_outputs_and_turn_switch(capsys):
    g = Game()
    sh = shell.PigShell(g, Scoreboard())
    sh.mode = "pvc"
    sh.brain = types.SimpleNamespace(decide=lambda game: "roll")

    # CPU to move -> force bust
    g.current_index = 1
    g.turn = Turn(g.current, g.dice)
    g.dice = OneDice()
    g.turn.dice = g.dice

    sh._cpu_take_turn()
    out = capsys.readouterr().out
    assert "CPU rolled 1" in out
    assert "CPU busted." in out
    # Turn should switch to Player 1 (human)
    assert g.current is g.players[0]


def test_do_quit_writes_scoreboard(tmp_path, monkeypatch, capsys):
    p = set_save_path(tmp_path, monkeypatch)

    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(10); b.add_score(8)
    sb.record(winner=a, players=[a, b], target=10)

    sh = shell.PigShell(Game(), sb)
    stop = sh.do_quit("")
    assert stop is True
    out = capsys.readouterr().out
    assert "Bye!" in out

    # file saved
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "history" in data and isinstance(data["history"], list)
    assert data["history"][0]["winner"] == "A"
