import pytest
from pig.game import Game
from pig.ai import ComputerStrategy, SmartStrategy


def _setup(game: Game, *, me_score=0, opp_score=0, turn_points=0,
           current_index=0, target=100):
    """Set up a game with specified scores, turn points, and target."""
    game.target = target
    game.players[0].score = me_score if current_index == 0 else opp_score
    game.players[1].score = opp_score if current_index == 0 else me_score
    game.current_index = current_index
    game.turn_points = turn_points
    return game


# ComputerStrategy (easy)
def test_computer_threshold_basic_roll_vs_hold():
    """Test ComputerStrategy rolls below threshold, holds at or above."""
    g = _setup(
        Game(),
        me_score=0,
        opp_score=0,
        turn_points=19,
        current_index=0,
        target=100
    )
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 20
    assert bot.decide(g) == "hold"


def test_computer_threshold_increases_when_behind():
    """Test threshold increases when behind by 10 points."""
    g = _setup(Game(), me_score=40, opp_score=50, turn_points=24,
               current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 25
    assert bot.decide(g) == "hold"


def test_computer_threshold_increases_large_gap():
    """Test threshold increases for large score gap (25 points)."""
    g = _setup(Game(), me_score=20, opp_score=45, turn_points=29,
               current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 30
    assert bot.decide(g) == "hold"


def test_computer_threshold_decreases_when_ahead():
    """Test threshold decreases when ahead by 20 points."""
    g = _setup(Game(), me_score=60, opp_score=40, turn_points=15,
               current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 16
    assert bot.decide(g) == "hold"


def test_computer_holds_if_win_now():
    """Test ComputerStrategy holds when turn points ensure a win."""
    g = _setup(Game(), me_score=95, opp_score=0, turn_points=5,
               current_index=0, target=100)
    bot = ComputerStrategy()
    assert bot.decide(g) == "hold"


def test_computer_boundary_gap_25():
    """Test threshold at exact gap of 25 points."""
    g = _setup(Game(), me_score=10, opp_score=35, turn_points=29,
               current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 30
    assert bot.decide(g) == "hold"


def test_computer_boundary_gap_10():
    """Test threshold at exact gap of 10 points."""
    g = _setup(Game(), me_score=30, opp_score=40, turn_points=24,
               current_index=0, target=100)
    bot = ComputerStrategy(base_threshold=20)
    assert bot.decide(g) == "roll"
    g.turn_points = 25
    assert bot.decide(g) == "hold"


def test_smart_never_holds_at_zero():
    """Test SmartStrategy always rolls when turn points are zero."""
    g = _setup(Game(), me_score=50, opp_score=50, turn_points=0,
               current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"


def test_smart_holds_if_win_now():
    """Test SmartStrategy holds when turn points ensure a win."""
    g = _setup(Game(), me_score=96, opp_score=10, turn_points=4,
               current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "hold"


def test_smart_endgame_requires_exact_finish():
    """Test SmartStrategy requires exact points to win in endgame."""
    g = _setup(Game(), me_score=97, opp_score=0, turn_points=2,
               current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 3
    assert bot.decide(g) == "hold"


def test_smart_big_gap_increases_threshold_beyond_max_cap():
    """Test threshold increases with large gap, respects max cap."""
    g = _setup(Game(), me_score=70, opp_score=100, turn_points=29,
               current_index=0, target=120)
    bot = SmartStrategy(min_threshold=12, max_threshold=28)
    assert bot.decide(g) == "roll"
    g.turn_points = 34
    assert bot.decide(g) == "hold"


def test_smart_when_ahead_reduces_threshold():
    """Test threshold reduces when ahead by 30 points."""
    g = _setup(Game(), me_score=90, opp_score=60, turn_points=13,
               current_index=0, target=110)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 14
    assert bot.decide(g) == "hold"


def test_smart_slightly_ahead_reduces_threshold():
    """Test threshold reduces when slightly ahead by 10 points."""
    g = _setup(Game(), me_score=80, opp_score=70, turn_points=15,
               current_index=0, target=100)
    bot = SmartStrategy()
    assert bot.decide(g) == "roll"
    g.turn_points = 16
    assert bot.decide(g) == "hold"