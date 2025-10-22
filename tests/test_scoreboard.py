# tests/test_scoreboard.py
import json
from pig.game import Game
from pig.player import Player
from pig.scoreboard import Scoreboard, ScoreRow


def _finish_game(target=10):
    """Make a finished game we can record."""
    g = Game(target=target)

    class SixDice:
        def roll(self): return 6

    # same dice for both Game and Turn so rolls are predictable
    g.dice = SixDice()
    g.turn.dice = g.dice

    # P1: 6 + 6 -> 12, hold -> winner
    g.roll(); g.roll(); g.hold()
    assert g.winner_id is not None, "expected a finished game"
    return g


# --- 1
def test_record_from_game_adds_row_with_winner_and_scores():
    sb = Scoreboard()
    g = _finish_game(target=10)

    sb.record_from_game(g)
    assert len(sb.history) == 1
    row = sb.history[0]
    assert isinstance(row, ScoreRow)
    assert row.target == 10
    assert row.winner == g.players[0].name  # P1 wins in this setup
    for p in g.players:
        assert row.scores[p.name] == p.score
    assert row.when and "T" in row.when  # basic ISO-ish sanity


# --- 2
def test_record_from_game_raises_if_not_finished():
    sb = Scoreboard()
    g = Game(target=50)  # no winner yet
    try:
        sb.record_from_game(g)
        assert False, "expected ValueError when recording unfinished game"
    except ValueError as e:
        assert "finished" in str(e)


# --- 3
def test_last_returns_recent_rows_in_order():
    sb = Scoreboard()
    # three quick manual rows
    a, b = Player("Alice"), Player("Bob")
    a.add_score(12); b.add_score(6)
    sb.record(winner=a, players=[a, b], target=10)

    c, d = Player("Carol"), Player("Dan")
    c.add_score(15); d.add_score(4)
    sb.record(winner=c, players=[c, d], target=15)

    e, f = Player("Eve"), Player("Frank")
    f.add_score(20); e.add_score(18)
    sb.record(winner=f, players=[e, f], target=20)

    last_two = sb.last(2)
    assert [r.winner for r in last_two] == [c.name, f.name]  # oldest→newest slice


# --- 4
def test_wins_table_and_top_aggregate_correctly():
    sb = Scoreboard()
    eve, bob, carol = Player("Eve"), Player("Bob"), Player("Carol")

    eve.add_score(21); bob.add_score(10)
    sb.record(winner=eve, players=[eve, bob], target=20)

    bob.reset_score(); eve.reset_score()
    bob.add_score(15); eve.add_score(14)
    sb.record(winner=bob, players=[bob, eve], target=15)

    eve.reset_score(); carol.reset_score()
    eve.add_score(12); carol.add_score(5)
    sb.record(winner=eve, players=[eve, carol], target=10)

    wins = sb.wins_table()
    assert wins["Eve"] == 2
    assert wins["Bob"] == 1
    assert "Carol" not in wins

    top2 = sb.top(2)
    assert top2[0] == ("Eve", 2)
    assert top2[1] == ("Bob", 1)


# --- 5
def test_reset_clears_history():
    sb = Scoreboard()
    sb.record_from_game(_finish_game())
    assert sb.history  # something is there

    sb.reset()
    assert sb.history == []


# --- 6
def test_to_dict_and_from_dict_roundtrip():
    sb = Scoreboard()
    sb.record_from_game(_finish_game(target=12))

    data = sb.to_dict()
    dumped = json.dumps(data)  # should serialize cleanly

    sb2 = Scoreboard.from_dict(json.loads(dumped))
    assert len(sb2.history) == 1
    r1, r2 = sb.history[0], sb2.history[0]
    assert r1.when == r2.when
    assert r1.target == r2.target
    assert r1.winner == r2.winner
    assert r1.scores == r2.scores


# --- 7
def test_last_with_more_requested_than_available_returns_all_in_order():
    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(10); b.add_score(5)
    sb.record(winner=a, players=[a, b], target=10)

    c, d = Player("C"), Player("D")
    d.add_score(12); c.add_score(3)
    sb.record(winner=d, players=[c, d], target=12)

    last = sb.last(10)  # ask for more than exists
    assert len(last) == 2
    assert [r.winner for r in last] == [a.name, d.name]


# --- 8
def test_top_breaks_ties_by_name_alphabetically():
    sb = Scoreboard()
    alice, bob, carol = Player("Alice"), Player("Bob"), Player("Carol")

    alice.add_score(10); bob.add_score(10); carol.add_score(10)
    sb.record(winner=carol, players=[alice, carol], target=10)
    sb.record(winner=bob,   players=[bob, carol],   target=10)
    sb.record(winner=alice, players=[alice, bob],   target=10)

    top3 = sb.top(3)
    assert top3 == [("Alice", 1), ("Bob", 1), ("Carol", 1)]


# --- 9
def test_from_dict_handles_empty_input():
    sb = Scoreboard.from_dict({})
    assert sb.history == []
    sb = Scoreboard.from_dict({"history": []})
    assert sb.history == []


# --- 10
def test_record_snapshot_uses_names_at_time_not_live_objects():
    sb = Scoreboard()
    p1, p2 = Player("Alice"), Player("Bob")
    p1.add_score(11); p2.add_score(7)
    sb.record(winner=p1, players=[p1, p2], target=10)

    # rename after recording; snapshot should keep the original names
    p1.change_name("Alicia")
    p2.change_name("Bobby")

    row = sb.history[0]
    assert row.winner == "Alice"
    assert set(row.scores.keys()) == {"Alice", "Bob"}
