# from src.pig.dice import Dice


# def test_roll_within_bounds():
#     """Dice roll should always be between 1 and 6."""
#     d = Dice()
#     for _ in range(20):
#         value = d.roll()
#         assert 1 <= value <= 6


# def test_custom_sides_and_error():
#     """Dice should handle custom sides and reject invalid ones."""
#     d = Dice(10)
#     assert 1 <= d.roll() <= 10

#     # should raise ValueError for sides < 2
#     try:
#         Dice(1)
#         assert False, "Expected ValueError for sides < 2"
#     except ValueError:
#         assert True

import random
import pytest
from src.pig.dice import Dice


def test_default_init_sets_six_sides():
    d = Dice()
    assert d.sides == 6


def test_custom_sides_values():
    # 6 assertions
    for sides in [2, 4, 6, 8, 12, 20]:
        d = Dice(sides)
        assert d.sides == sides


def test_invalid_sides_raises_valueerror():
    # 3 assertions via three bad inputs
    for bad in [0, 1, -3]:
        with pytest.raises(ValueError) as exc:
            Dice(bad)
        assert "at least 2 sides" in str(exc.value)


def test_type_error_when_non_int_sides():
    with pytest.raises(TypeError):
        # Triggers a TypeError from the '<' comparison in __init__
        Dice("6")  # type: ignore[arg-type]


def test_roll_returns_int_multiple_times():
    # 10 assertions
    d = Dice()
    for _ in range(10):
        assert isinstance(d.roll(), int)


def test_roll_in_range_default_many():
    # 20 assertions
    d = Dice()
    for _ in range(20):
        v = d.roll()
        assert 1 <= v <= 6


def test_roll_in_range_custom_sides():
    # 15 assertions total (3*5)
    for sides in [3, 7, 10]:
        d = Dice(sides)
        for _ in range(5):
            v = d.roll()
            assert 1 <= v <= sides


def test_roll_not_constant_over_trials():
    d = Dice()
    rolls = {d.roll() for _ in range(50)}
    # at least two distinct outcomes should appear
    assert len(rolls) >= 2


def test_seed_makes_results_reproducible():
    d = Dice()
    random.seed(12345)
    seq1 = [d.roll() for _ in range(8)]
    random.seed(12345)
    seq2 = [d.roll() for _ in range(8)]
    assert len(seq1) == 8
    assert seq1 == seq2


def test_mutating_sides_affects_range():
    # shows the object uses self.sides at call time
    d = Dice(6)
    d.sides = 3
    for _ in range(6):
        v = d.roll()
        assert 1 <= v <= 3
