import pytest

from pig.game import Game
from pig.turn import Turn
from pig.player import Player


# ---------- helpers ----------

class OneDice:
    """A dice class that always rolls a value of 1."""

    def roll(self):
        """Return a constant dice roll value of 1."""
        return 1


class ConstDice:
    """A dice class that always returns a constant value."""

    def __init__(self, v):
        """Initialize ConstDice with a constant value v."""
        self.v = v

    def roll(self):
        """Return the constant dice roll value."""
        return self.v


class SeqDice:
    """A dice class that returns values from a sequence, one at a time."""

    def __init__(self, seq):
        """Initialize SeqDice with a sequence of values."""
        self.seq = list(seq)

    def roll(self):
        """Return the next value in the sequence."""
        return self.seq.pop(0)

class AlwaysRoll:
    """Always roll."""

    def decide(self, game: Game) -> str:
        """Decide."""
        return "roll"

class RollOnceThenHold:
     """Roll once and hold."""

    def __init__(self):
        """Initialize the counter."""
        self.n = 0
    def decide(self, game: Game) -> str:
        """Roll once then hold on subsequent calls."""
        self.n += 1
        return "roll" if self.n == 1 else "hold"
class AlwaysHold:
    def decide(self, game: Game) -> str:
        """Always hold without rolling."""
        return "hold"
        return "hold"


# ---------- tests ----------

def test_init_sets_turn_for_player1_and_defaults():
    g = Game()
    assert isinstance(g.turn, Turn)
    assert g.current.name == "Player 1"
    assert g.opponent.name == "Player 2"
    assert g.turn.player is g.current
    assert g.turn_points == 0
    assert g.winner_id is None
    # turn shares the game's dice by default
    assert g.turn.dice is g.dice


def test_roll_accumulates_then_busts_and_switches():
    g = Game()
    g.dice = SeqDice([3, 4, 1])   # +3, +4, then bust
    g.turn.dice = g.dice

    assert g.roll() == 3
    assert g.turn_points == 3
    assert g.current.name == "Player 1"

    assert g.roll() == 4
    assert g.turn_points == 7
    assert g.current.name == "Player 1"

    # bust switches to Player 2 and clears turn points
    assert g.roll() == 1
    assert g.turn_points == 0
    assert g.current.name == "Player 2"
    # new Turn created for the new current player
    assert isinstance(g.turn, Turn)
    assert g.turn.player is g.current


def test_hold_banks_points_and_switches_when_no_win():
    g = Game()
    g.dice = ConstDice(5)
    g.turn.dice = g.dice

    g.roll(); g.roll()   # 10
    g.hold()
    assert g.players[0].score == 10
    assert g.turn_points == 0
    assert g.current.name == "Player 2"


def test_reaching_target_sets_winner_and_blocks_future_actions():
    g = Game(target=12)
    g.dice = ConstDice(6)
    g.turn.dice = g.dice

    # P1: 6+6=12 -> hold = win
    g.roll(); g.roll(); g.hold()
    assert g.is_over
    assert g.get_winner() is g.players[0]

    # further rolls are ignored
    before = (g.current_index, g.players[0].score, g.players[1].score, g.turn_points)
    assert g.roll() == 0
    g.hold()
    after = (g.current_index, g.players[0].score, g.players[1].score, g.turn_points)
    assert before == after


def test_reset_keep_names_true_and_false():
    g = Game()
    g.players[0].change_name("Alice")
    g.players[1].change_name("Bob")

    # give Alice some points
    g.dice = ConstDice(6); g.turn.dice = g.dice
    g.roll(); g.hold()
    assert g.players[0].score == 6

    g.reset(keep_names=True)
    assert [p.name for p in g.players] == ["Alice", "Bob"]
    assert g.players[0].score == 0 and g.players[1].score == 0
    assert g.current.name == "Alice"
    assert isinstance(g.turn, Turn) and g.turn.player is g.current

    g.reset(keep_names=False)
    assert [p.name for p in g.players] == ["Player 1", "Player 2"]
    assert g.current.name == "Player 1"


def test_set_target_validation_and_assignment():
    g = Game()
    with pytest.raises(TypeError):
        g.set_target("100")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        g.set_target(0)
    g.set_target(25)
    assert g.target == 25


def test_rename_validation_and_effect():
    g = Game()
    with pytest.raises(ValueError):
        g.rename(3, "X")
    g.rename(1, "Alice")
    g.rename(2, "Bob")
    assert [p.name for p in g.players] == ["Alice", "Bob"]


def test_snapshot_contains_expected_fields_and_values():
    g = Game(target=15)
    g.players[0].change_name("Alice")
    g.players[1].change_name("Bob")
    g.dice = ConstDice(5); g.turn.dice = g.dice
    g.roll(); g.roll()  # 10
    snap = g.snapshot()
    assert set(snap.keys()) == {"target", "current", "turn_points", "scores", "winner"}
    assert snap["target"] == 15
    assert snap["current"] == "Alice"
    assert snap["turn_points"] == 10
    assert snap["scores"]["Alice"] == 0  # not banked yet
    assert snap["winner"] is None


def test_is_over_and_get_winner_progression():
    g = Game(target=6)
    assert not g.is_over and g.get_winner() is None
    g.dice = ConstDice(6); g.turn.dice = g.dice
    g.roll(); g.hold()
    assert g.is_over
    assert g.get_winner() == g.players[0]


def test_turn_uses_games_dice_instance_when_replaced():
    g = Game()
    d = ConstDice(2)
    g.dice = d
    g.turn.dice = g.dice
    g.roll(); g.roll()
    assert g.turn_points == 4


def test_play_cpu_turn_rolls_until_bust():
    g = Game()
    # make it Player 2's turn
    g.current_index = 1
    g.turn = Turn(g.current, g.dice)

    g.dice = OneDice()         # first roll => bust
    g.turn.dice = g.dice

    result = g.play_cpu_turn(AlwaysRoll().decide)
    assert result["ended"] == "bust"
    assert result["actions"][0] == {"action": "roll", "value": 1}
    # turn should now belong to Player 1
    assert g.current is g.players[0]


def test_play_cpu_turn_roll_then_hold_and_report_next_player():
    g = Game()
    # Player 2 to move
    g.current_index = 1
    g.turn = Turn(g.current, g.dice)

    g.dice = ConstDice(4)
    g.turn.dice = g.dice

    result = g.play_cpu_turn(RollOnceThenHold().decide)
    # Should have one roll and one hold action
    assert [a["action"] for a in result["actions"]] == ["roll", "hold"]
    assert result["ended"] == "hold"
    # After CPU's hold, turn should switch to Player 1
    assert g.current is g.players[0]
    assert result["next"] == g.current.name


def test_play_cpu_turn_can_win_and_returns_win_result():

    g = Game(target=10)
    # ensure Player 1 is to play and wins by holding
    g.current_index = 0
    g.turn = Turn(g.current, g.dice)
    # give current turn some points so holding wins now
    g.turn.points = 10
    g.turn.finished = False
    g.turn.busted = False

    result = g.play_cpu_turn(AlwaysHold().decide)
    assert result["ended"] == "win"
    assert g.is_over
    assert g.get_winner() is g.players[0]
