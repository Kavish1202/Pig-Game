import json
from pig.game import Game
from pig.player import Player
from pig.scoreboard import Scoreboard, ScoreRow


def _finish_game(target=10):
    """Create a finished game with predictable rolls for recording."""
    g = Game(target=target)

    class SixDice:
        def roll(self):
            return 6

    # Same dice for Game and Turn for predictable rolls
    g.dice = SixDice()
    g.turn.dice = g.dice

    # P1: 6 + 6 -> 12, hold -> winner
    g.roll()
    g.roll()
    g.hold()
    assert g.winner_id is not None, "Expected a finished game"
    return g


def test_record_from_game_adds_row_with_winner_and_scores():
    """Test recording a finished game adds a row with winner and scores."""
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
    assert row.when and "T" in row.when  # Basic ISO-ish sanity check


def test_record_from_game_raises_if_not_finished():
    """Test recording an unfinished game raises ValueError."""
    sb = Scoreboard()
    g = Game(target=50)  # No winner yet
    try:
        sb.record_from_game(g)
        assert False, "Expected ValueError for unfinished game"
    except ValueError as e:
        assert "finished" in str(e)


def test_last_returns_recent_rows_in_order():
    """Test last() returns recent rows in chronological order."""
    sb = Scoreboard()
    a, b = Player("Alice"), Player("Bob")
    a.add_score(12)
    b.add_score(6)
    sb.record(winner=a, players=[a, b], target=10)

    c, d = Player("Carol"), Player("Dan")
    c.add_score(15)
    d.add_score(4)
    sb.record(winner=c, players=[c, d], target=15)

    e, f = Player("Eve"), Player("Frank")
    f.add_score(20)
    e.add_score(18)
    sb.record(winner=f, players=[e, f], target=20)

    last_two = sb.last(2)
    assert [r.winner for r in last_two] == [c.name, f.name]  # Oldest to newest


def test_wins_table_and_top_aggregate_correctly():
    """Test wins_table counts wins and top returns sorted results."""
    sb = Scoreboard()
    eve, bob, carol = Player("Eve"), Player("Bob"), Player("Carol")

    eve.add_score(21)
    bob.add_score(10)
    sb.record(winner=eve, players=[eve, bob], target=20)

    bob.reset_score()
    eve.reset_score()
    bob.add_score(15)
    eve.add_score(14)
    sb.record(winner=bob, players=[bob, eve], target=15)

    eve.reset_score()
    carol.reset_score()
    eve.add_score(12)
    carol.add_score(5)
    sb.record(winner=eve, players=[eve, carol], target=10)

    wins = sb.wins_table()
    assert wins["Eve"] == 2
    assert wins["Bob"] == 1
    assert "Carol" not in wins

    top2 = sb.top(2)
    assert top2[0] == ("Eve", 2)
    assert top2[1] == ("Bob", 1)


def test_reset_clears_history():
    """Test reset clears the scoreboard history."""
    sb = Scoreboard()
    sb.record_from_game(_finish_game())
    assert sb.history  # History is non-empty

    sb.reset()
    assert sb.history == []


def test_to_dict_and_from_dict_roundtrip():
    """Test to_dict and from_dict preserve scoreboard data."""
    sb = Scoreboard()
    sb.record_from_game(_finish_game(target=12))

    data = sb.to_dict()
    dumped = json.dumps(data)  # Should serialize cleanly

    sb2 = Scoreboard.from_dict(json.loads(dumped))
    assert len(sb2.history) == 1
    r1, r2 = sb.history[0], sb2.history[0]
    assert r1.when == r2.when
    assert r1.target == r2.target
    assert r1.winner == r2.winner
    assert r1.scores == r2.scores


def test_last_with_more_requested_than_available_returns_all_in_order():
    """Test last() returns all rows in order when requesting more than available."""
    sb = Scoreboard()
    a, b = Player("A"), Player("B")
    a.add_score(10)
    b.add_score(5)
    sb.record(winner=a, players=[a, b], target=10)

    c, d = Player("C"), Player("D")
    d.add_score(12)
    c.add_score(3)
    sb.record(winner=d, players=[c, d], target=12)

    last = sb.last(10)  # Ask for more than exists
    assert len(last) == 2
    assert [r.winner for r in last] == [a.name, d.name]


def test_top_breaks_ties_by_name_alphabetically():
    """Test top() sorts tied players alphabetically by name."""
    sb = Scoreboard()
    alice, bob, carol = Player("Alice"), Player("Bob"), Player("Carol")

    alice.add_score(10)
    bob.add_score(10)
    carol.add_score(10)
    sb.record(winner=carol, players=[alice, carol], target=10)
    sb.record(winner=bob, players=[bob, carol], target=10)
    sb.record(winner=alice, players=[alice, bob], target=10)

    top3 = sb.top(3)
    assert top3 == [("Alice", 1), ("Bob", 1), ("Carol", 1)]


def test_from_dict_handles_empty_input():
    """Test from_dict handles empty or minimal input correctly."""
    sb = Scoreboard.from_dict({})
    assert sb.history == []
    sb = Scoreboard.from_dict({"history": []})
    assert sb.history == []


def test_record_snapshot_uses_names_at_time_not_live_objects():
    """Test record uses player names at the time of recording."""
    sb = Scoreboard()
    p1, p2 = Player("Alice"), Player("Bob")
    p1.add_score(11)
    p2.add_score(7)
    sb.record(winner=p1, players=[p1, p2], target=10)

    # Rename after recording; snapshot should keep original names
    p1.change_name("Alicia")
    p2.change_name("Bobby")

    row = sb.history[0]
    assert row.winner == "Alice"
    assert set(row.scores.keys()) == {"Alice", "Bob"}