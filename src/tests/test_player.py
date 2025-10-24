import pytest
from pig.player import Player


def test_default_init_values():
    p = Player()
    assert isinstance(p.player_id, str)
    assert p.name == "Player"
    assert p.score == 0


def test_custom_name_is_trimmed_and_set():
    p = Player("  Alice  ")
    assert p.name == "Alice"
    assert p.score == 0


def test_empty_or_whitespace_name_raises():
    for bad in ["", "   ", None]:
        with pytest.raises(ValueError):
            Player(bad)  # type: ignore[arg-type]


def test_change_name_keeps_id_and_trims():
    p = Player("Bob")
    original_id = p.player_id
    p.change_name("  Bobby  ")
    assert p.name == "Bobby"
    assert p.player_id == original_id  # id is stable across renames


def test_change_name_rejects_empty():
    p = Player("X")
    for bad in ["", "   ", None]:
        with pytest.raises(ValueError):
            p.change_name(bad)  # type: ignore[arg-type]


def test_add_score_increments_and_accepts_zero():
    p = Player("Y")
    p.add_score(0)
    assert p.score == 0
    p.add_score(5)
    assert p.score == 5
    p.add_score(7)
    assert p.score == 12


def test_add_score_rejects_negative_and_non_int():
    p = Player("Z")
    with pytest.raises(ValueError):
        p.add_score(-1)
    with pytest.raises(TypeError):
        p.add_score(3.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        p.add_score("10")  # type: ignore[arg-type]


def test_reset_score_sets_zero():
    p = Player("W")
    p.add_score(9)
    p.reset_score()
    assert p.score == 0


def test_str_contains_name_and_score():
    p = Player("Mia")
    p.add_score(3)
    s = str(p)
    assert "Mia" in s
    assert "3" in s
    assert "pts" in s


def test_to_dict_roundtrip_fields_present_and_consistent():
    p = Player("Kai")
    p.add_score(4)
    data = p.to_dict()
    assert set(data.keys()) == {"player_id", "name", "score"}
    assert data["player_id"] == p.player_id
    assert data["name"] == "Kai"
    assert data["score"] == 4
