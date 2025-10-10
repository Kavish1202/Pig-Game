from pig.game import Game


def test_game_starts_with_player1_and_zero_turn_points():
    g = Game()
    assert g.current.name == "Player 1"
    assert g.turn_points == 0
    assert g.winner_id is None


def test_roll_accumulates_until_one_then_switches():
    g = Game()
    # monkeypatch by swapping dice with deterministic values via a stub
    class StubDice:
        seq = [3, 4, 1]  # accumulate 3+4, then bust on 1
        def roll(self):
            return self.seq.pop(0)
    g.dice = StubDice()  # type: ignore[assignment]

    assert g.roll() == 3
    assert g.turn_points == 3
    assert g.current.name == "Player 1"

    assert g.roll() == 4
    assert g.turn_points == 7
    assert g.current.name == "Player 1"

    # bust: turn_points reset and turn switches
    assert g.roll() == 1
    assert g.turn_points == 0
    assert g.current.name == "Player 2"


def test_hold_banks_points_and_switches_turn():
    g = Game()
    class StubDice:
        def roll(self): return 5
    g.dice = StubDice()  # type: ignore[assignment]

    g.roll(); g.roll()   # +5 +5 = 10 turn points
    g.hold()
    assert g.players[0].score == 10
    assert g.turn_points == 0
    assert g.current.name == "Player 2"


def test_reaching_target_sets_winner_and_stops_changes():
    g = Game(target=15)
    class StubDice:
        def __init__(self): self.n = 0
        def roll(self):
            self.n += 1
            return 6  # always 6
    g.dice = StubDice()  # type: ignore[assignment]

    # P1 rolls 6,6 → 12; holds → score=12
    g.roll(); g.roll(); g.hold()
    assert g.players[0].score == 12
    assert g.winner_id is None

    # P2 rolls once (6), holds → score=6
    g.roll(); g.hold()
    assert g.players[1].score == 6
    assert g.winner_id is None

    # P1 rolls once (6), holds → 12+6=18 >= 15 → winner
    g.roll(); g.hold()
    assert g.winner_id == g.players[0].player_id

    # further actions do nothing harmful
    before_scores = (g.players[0].score, g.players[1].score)
    g.roll(); g.hold()
    after_scores = (g.players[0].score, g.players[1].score)
    assert before_scores == after_scores


def test_reset_keeps_names_by_default_and_clears_scores():
    g = Game()
    g.players[0].name = "Alice"
    g.players[1].name = "Bob"
    # simulate some state
    class StubDice: 
        def roll(self): return 6
    g.dice = StubDice()  # type: ignore[assignment]
    g.roll(); g.hold()   # Alice banks 6

    g.reset()  # keep_names=True default
    assert g.players[0].name == "Alice"
    assert g.players[1].name == "Bob"
    assert g.players[0].score == 0
    assert g.players[1].score == 0
    assert g.current.name == "Player 1"  # turn reset

def test_hold_with_zero_turn_points_switches_without_score_change():
    g = Game()
    p1_before = g.players[0].score
    p2_before = g.players[1].score

    # Holding with 0 should not change scores, but should switch the turn
    g.hold()
    assert g.players[0].score == p1_before
    assert g.players[1].score == p2_before
    assert g.current.name == "Player 2"


def test_opponent_property_tracks_inverse_of_current():
    g = Game()
    # At start: current=P1, opponent=P2
    assert g.current.name == "Player 1"
    assert g.opponent.name == "Player 2"

    # Force a switch (bust on 1)
    class OneDice:
        def roll(self): return 1
    g.dice = OneDice()  # type: ignore[assignment]

    g.roll()  # bust -> switch
    assert g.current.name == "Player 2"
    assert g.opponent.name == "Player 1"


def test_roll_is_ignored_after_game_over_and_state_does_not_change():
    g = Game(target=5)

    class SixDice:
        def roll(self): return 6
    g.dice = SixDice()  # type: ignore[assignment]

    # Win immediately on first hold
    g.roll()            # turn_points=6
    g.hold()            # score P1=6 -> winner
    assert g.winner_id == g.players[0].player_id

    # Capture state before attempting more actions
    before = (
        g.current_index,
        g.turn_points,
        g.players[0].score,
        g.players[1].score,
    )

    # Further rolls should return 0 and not change anything
    assert g.roll() == 0
    after = (
        g.current_index,
        g.turn_points,
        g.players[0].score,
        g.players[1].score,
    )
    assert before == after


def test_reset_without_keep_names_resets_to_default_names_and_clears():
    g = Game()
    g.players[0].name = "Alice"
    g.players[1].name = "Bob"

    class SixDice:
        def roll(self): return 6
    g.dice = SixDice()  # type: ignore[assignment]

    g.roll()  # Alice collects 6
    g.hold()  # Alice banks 6

    g.reset(keep_names=False)
    assert g.players[0].name == "Player 1"
    assert g.players[1].name == "Player 2"
    assert g.players[0].score == 0
    assert g.players[1].score == 0
    assert g.turn_points == 0
    assert g.winner_id is None
    assert g.current.name in {"Player 1", "Alice", "Bob"}  # turn reset to index 0


def test_not_winner_until_hold_even_if_turn_points_meet_target():
    g = Game(target=10)

    class SixDice:
        def roll(self): return 6
    g.dice = SixDice()  # type: ignore[assignment]

    # Two rolls -> turn_points = 12 >= target, but no winner yet
    g.roll()
    g.roll()
    assert g.turn_points >= 10
    assert g.winner_id is None

    # Winner only determined on hold
    g.hold()
    assert g.winner_id == g.players[0].player_id