import pytest
from pig.game import Game
from pig.ai import ComputerStrategy, SmartStrategy


def _setup(game: Game, *, me_score=0, opp_score=0, turn_points=0, current_index=0, target=100):
    game.target = target
    game.players[0].score = me_score if current_index == 0 else opp_score
    game.players[1].score = opp_score if current_index == 0 else me_score
    game.current_index = current_index
    game.turn_points = turn_points
    return game


# --------------------------
# ComputerStrategy (easy)
# --------------------------

def test_computer_threshold_basic_roll_vs_hold():
    g = _setup(Game(), me_score=0, opp_score=0, turn_points=19, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"

    g.turn_points = 20
    assert bot.decide(g) == "hold"


def test_computer_threshold_increases_when_behind():
    # gap = +10 (we're behind) -> threshold = 20 + 5 = 25
    g = _setup(Game(), me_score=40, opp_score=50, turn_points=24, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 25
    assert bot.decide(g) == "hold"


def test_computer_threshold_increases_large_gap():
    # gap = +25 (we're behind) -> threshold = 20 + 10 = 30
    g = _setup(Game(), me_score=20, opp_score=45, turn_points=29, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 30
    assert bot.decide(g) == "hold"


def test_computer_threshold_decreases_when_ahead():
    # gap = -20 (we're ahead by 20) -> threshold = 20 - 4 = 16
    g = _setup(Game(), me_score=60, opp_score=40, turn_points=15, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 16
    assert bot.decide(g) == "hold"


def test_computer_holds_if_win_now():
    g = _setup(Game(), me_score=95, opp_score=0, turn_points=5, current_index=0, target=100)
    bot = ComputerStrategy()
    assert bot.decide(g) == "hold"


def test_computer_boundary_gap_25():
    # gap = +25 exactly -> threshold = 20 + 10 = 30
    g = _setup(Game(), me_score=10, opp_score=35, turn_points=29, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 30
    assert bot.decide(g) == "hold"


def test_computer_boundary_gap_10():
    # gap = +10 exactly -> threshold = 20 + 5 = 25
    g = _setup(Game(), me_score=30, opp_score=40, turn_points=24, current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 25
    assert bot.decide(g) == "hold"


# --------------------------
# SmartStrategy (normal/hard)
# --------------------------

def test_smart_never_holds_at_zero():
    g = _setup(Game(), me_score=50, opp_score=50, turn_points=0, current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"


def test_smart_holds_if_win_now():
    g = _setup(Game(), me_score=96, opp_score=10, turn_points=4, current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "hold"


def test_smart_endgame_requires_exact_finish():
    # points_needed = 3 (<=8): must have t >= 3 to hold; else roll
    g = _setup(Game(), me_score=97, opp_score=0, turn_points=2, current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 3
    assert bot.decide(g) == "hold"


def test_smart_big_gap_increases_threshold_beyond_max_cap():
    # points_needed = 50 -> base threshold = (50//2)+8 = 33, clamped to max=28
    # big gap (behind by 30) -> +6 => 34 after clamp
    g = _setup(Game(), me_score=70, opp_score=100, turn_points=29, current_index=0, target=120)
    bot = SmartStrategy(min_threshold=12, max_threshold=28)
    assert bot.decide(g) == "roll"
    g.turn_points = 34
    assert bot.decide(g) == "hold"


def test_smart_when_ahead_reduces_threshold():
    # points_needed = 20 -> base 18; ahead by 30 (gap = -30) -> -4 => threshold 14
    g = _setup(Game(), me_score=90, opp_score=60, turn_points=13, current_index=0, target=110)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 14
    assert bot.decide(g) == "hold"


def test_smart_slightly_ahead_reduces_threshold():
    # points_needed = 20 -> base 18; ahead by 10 (gap = -10) -> -2 => threshold 16
    g = _setup(Game(), me_score=80, opp_score=70, turn_points=15, current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 16
    assert bot.decide(g) == "hold"