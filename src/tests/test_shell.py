import builtins
import json
import types
import pytest

from pig.game import Game
from pig.player import Player
from pig.turn import Turn
from pig.scoreboard import Scoreboard
import pig.shell as shell


# simple deterministic dice
class ConstDice:
    def __init__(self, v):
        self.v = v
    def roll(self):
        return self.v

class SeqDice:
    def __init__(self, seq):
        self.seq = list(seq)
    def roll(self):
        return self.seq.pop(0)


def set_tmp_save_path(tmp_path, monkeypatch):
    p = tmp_path / "scoreboard.json"
    monkeypatch.setattr(shell, "SAVE_PATH", p, raising=True)
    return p


# 1) load/save scoreboard happy path + broken json fallback
def test_load_save_scoreboard(tmp_path, monkeypatch):
    p = set_tmp_save_path(tmp_path, monkeypatch)

    # nothing yet -> new empty scoreboard
    sb = shell.load_scoreboard()
    assert isinstance(sb, Scoreboard)
    assert sb.last(1) == []

    # write one record and save
    a, b = Player("A"), Player("B")
    a.add_score(10); b.add_score(6)
    sb.record(winner=a, players=[a, b], target=10)
    shell.save_scoreboard(sb)
    assert p.exists()

    # load back (valid json)
    sb2 = shell.load_scoreboard()
    rows = sb2.last(1)
    assert rows and rows[0].winner == "A"

    # break the json and expect a fresh scoreboard
    p.write_text("{ not json", encoding="utf-8")
    sb3 = shell.load_scoreboard()
    assert isinstance(sb3, Scoreboard)
    assert sb3.last(1) == []


# 2) starting prompts: choose pvc + hard, brain set, p2 named Computer
def test_startup_prompt_pvc_hard(monkeypatch, capsys):
    inputs = iter(["2", "3"])  # pvc, then hard
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


# 3) starting prompt pvp (no diff ask)
def test_startup_prompt_pvp(monkeypatch, capsys):
    inputs = iter(["1"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()
    assert sh.mode == "pvp"
    assert sh.brain is None
    out = capsys.readouterr().out
    assert "Mode set to pvp" in out


# 4) do_status prints header
def test_do_status_prints_header(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    # don’t prompt here; just call print helpers
    sh._print_header()
    sh.do_status("")
    out = capsys.readouterr().out
    assert "Pig — first to" in out
    assert "Current:" in out


# 5) roll then bust path (prints a bunch of lines), and normal roll
def test_do_roll_normal_then_bust(capsys):
    g = Game()
    g.dice = SeqDice([5, 1])
    g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    sh.do_roll("")
    out1 = capsys.readouterr().out
    assert "Rolled 5" in out1
    assert "Turn points: 5" in out1

    sh.do_roll("")
    out2 = capsys.readouterr().out
    assert "Rolled 1." in out2
    assert "BUSTED! No points this turn." in out2
    assert "Score this round: 0 points." in out2
    assert "Total score:" in out2
    assert "turn." in out2


# 6) hold banks and announces next turn
def test_do_hold_banks(capsys):
    g = Game()
    g.dice = ConstDice(6)
    g.turn.dice = g.dice
    sh = shell.PigShell(g, Scoreboard())

    sh.do_roll(""); sh.do_roll("")  # 12 points
    sh.do_hold("")
    out = capsys.readouterr().out
    assert "Holding. Current Score:" in out
    assert "turn." in out


# 7) rename player ok + usage error
def test_do_name_success_and_usage(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_name("1 Alice")
    assert sh.game.players[0].name == "Alice"
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1  # header refresh

    sh.do_name("oops")
    out2 = capsys.readouterr().out
    assert "Usage: name 1 Alice" in out2


# 8) target success + error
def test_do_target_ok_and_error(capsys):
    sh = shell.PigShell(Game(), Scoreboard())
    sh.do_target("150")
    out1 = capsys.readouterr().out
    assert "Target set to 150." in out1
    assert sh.game.target == 150

    sh.do_target("x")
    out2 = capsys.readouterr().out
    assert "Could not set target:" in out2


# 9) reset keep and clear names
def test_do_reset_keep_and_clear(capsys):
    g = Game()
    g.players[0].change_name("Alice")
    g.players[1].change_name("Bob")
    sh = shell.PigShell(g, Scoreboard())

    # give some score
    g.dice = ConstDice(6); g.turn.dice = g.dice
    sh.do_roll(""); sh.do_hold("")
    assert g.players[0].score == 6

    sh.do_reset("keep")
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1
    assert [p.name for p in g.players] == ["Alice", "Bob"]
    assert g.players[0].score == 0

    sh.do_reset("clear")
    out2 = capsys.readouterr().out
    assert [p.name for p in g.players] == ["Player 1", "Player 2"]


# 10) view prints recent results; save writes file
def test_view_and_save(tmp_path, monkeypatch, capsys):
    p = set_tmp_save_path(tmp_path, monkeypatch)
    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(7); b.add_score(5)
    sb.record(winner=a, players=[a, b], target=10)

    sh = shell.PigShell(Game(), sb)
    sh.do_view("")
    out = capsys.readouterr().out
    assert "Recent results:" in out
    assert "winner: A" in out

    sh.do_save("")
    out2 = capsys.readouterr().out
    assert "Scoreboard saved to" in out2
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "history" in data


# 11) mode/diff switching and bad inputs
def test_mode_and_diff_switching_and_errors(capsys):
    sh = shell.PigShell(Game(), Scoreboard())

    sh.do_mode("pvc")
    assert sh.mode == "pvc" and sh.brain is not None
    out1 = capsys.readouterr().out
    assert "Pig — first to" in out1

    sh.do_diff("hard")
    assert sh.difficulty == "hard"
    out2 = capsys.readouterr().out
    assert "Difficulty set to hard." in out2

    sh.do_mode("pvp")
    assert sh.mode == "pvp" and sh.brain is None

    sh.do_mode("nope")
    out3 = capsys.readouterr().out
    assert "Pick 'pvp' or 'pvc'." in out3

    sh.do_diff("banana")
    out4 = capsys.readouterr().out
    assert "Pick 'easy', 'normal' or 'hard'." in out4


# 12) cpu turn printing, default() unknown + cheat unlock + menu ops (minimal)
def test_cpu_turn_and_cheat_menu(monkeypatch, capsys, tmp_path):
    # isolate save path for winner record later
    set_tmp_save_path(tmp_path, monkeypatch)

    g = Game()
    sb = Scoreboard()
    sh = shell.PigShell(g, sb)

    # make it pvc with a dumb brain
    sh.mode = "pvc"
    sh.brain = types.SimpleNamespace(decide=lambda game: "roll")

    # let CPU (p2) play and bust immediately
    g.current_index = 1
    g.turn = Turn(g.current, g.dice)
    g.dice = ConstDice(1)      # instant bust
    g.turn.dice = g.dice

    sh._cpu_take_turn()
    out = capsys.readouterr().out
    assert "rolled 1" in out
    assert "CPU busted." in out
    assert g.current is g.players[0]  # switched turn

    # unknown command goes to default()
    sh.default("nonsense-cmd")
    out2 = capsys.readouterr().out
    assert "Unknown command:" in out2

    # now unlock cheat menu: feed a few simple commands, then back
    # we keep it short to avoid over-coupling to prints
    cheat_inputs = iter([
        "next 6 6",   # force rolls
        "add 1 5",    # give points
        "score 2 11",
        "clear",
        "back"
    ])
    monkeypatch.setattr(builtins, "input", lambda _: next(cheat_inputs))

    # trigger default -> magic word -> menu -> consume inputs -> return
    sh.default(sh._cheat_word)
    out3 = capsys.readouterr().out
    assert "(dev) cheats unlocked." in out3
    assert "cheat menu" in out3
    assert "ok." in out3 or "cleared." in out3  # at least one operation echoed

    # sanity: after cheat ops above, we're back to normal prompt
    # also: queue should be cleared by the "clear" command
    # force a non-busted normal roll path to confirm shell still works
    g.dice = ConstDice(4); g.turn.dice = g.dice
    sh.do_roll("")
    out4 = capsys.readouterr().out
    assert "Rolled 4. Turn points: 4" in out4


# edge: preloop calls both prompt and print header -> exercise once fully
def test_preloop_entire_flow(monkeypatch, capsys):
    inputs = iter(["2", "2"])  # pvc + normal
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    sh = shell.PigShell(Game(), Scoreboard())
    sh.preloop()
    out = capsys.readouterr().out
    assert "Mode set to pvc (normal)" in out
    assert "Pig — first to" in out
    assert "Current:" in out


# edge: postcmd does winner check paths; simulate a win then ensure it resets/records
def test_postcmd_records_and_resets(monkeypatch, tmp_path, capsys):
    set_tmp_save_path(tmp_path, monkeypatch)
    g = Game(target=6)
    sb = Scoreboard()
    sh = shell.PigShell(g, sb)

    # give P1 enough turn points to win on hold, then call postcmd to process
    g.turn.points = 6
    # simulate that a command (e.g., hold) was just run; we call postcmd to process winner
    # holding from within the loop is done by do_hold, but we hit the same branch by setting winner and calling postcmd
    g.current.add_score(6)
    g.winner_id = g.current.player_id

    # postcmd should record, save, reset, and print a new header
    stop = sh.postcmd(False, "whatever")
    assert stop is False
    out = capsys.readouterr().out
    assert "wins with" in out
    assert "Recent results:" in out
    assert "Pig — first to" in out
    # after reset winner cleared
    assert not g.is_over
