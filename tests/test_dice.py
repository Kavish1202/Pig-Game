from src.pig.dice import Dice


def test_roll_within_bounds():
    """Dice roll should always be between 1 and 6."""
    d = Dice()
    for _ in range(20):
        value = d.roll()
        assert 1 <= value <= 6


def test_custom_sides_and_error():
    """Dice should handle custom sides and reject invalid ones."""
    d = Dice(10)
    assert 1 <= d.roll() <= 10

    # should raise ValueError for sides < 2
    try:
        Dice(1)
        assert False, "Expected ValueError for sides < 2"
    except ValueError:
        assert True
