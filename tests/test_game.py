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
