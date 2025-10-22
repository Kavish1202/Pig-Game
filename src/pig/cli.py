"""Tiny CLI to play Pig in the terminal."""
from __future__ import annotations
import json
from pathlib import Path
from time import sleep

from pig.ai import ComputerStrategy, SmartStrategy
from pig.game import Game
from pig.scoreboard import Scoreboard


SAVE_PATH = Path("scoreboard.json")


def load_scoreboard() -> Scoreboard:
    if SAVE_PATH.exists():
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            return Scoreboard.from_dict(data)
        except Exception:
            return Scoreboard()
    return Scoreboard()


def save_scoreboard(sb: Scoreboard) -> None:
    SAVE_PATH.write_text(json.dumps(sb.to_dict(), indent=2), encoding="utf-8")


def print_header(game: Game) -> None:
    print("=" * 42)
    print(f"Pig — first to {game.target} wins")
    print("-" * 42)
    p1, p2 = game.players
    print(f"{p1.name:>12}: {p1.score:>3}   vs   {p2.name:<12}: {p2.score:>3}")
    print("-" * 42)


def print_turn(game: Game, mode: str, is_cpu_p2: bool) -> None:
    print(f"Current: {game.current.name}")
    print(f"Turn points: {game.turn_points}")
    if mode == "pvc" and is_cpu_p2 and game.current is game.players[1]:
        print("Computer is thinking…")
    else:
        print("Commands: [r]oll  [h]old  [s]tatus  re[n]ame  [t]arget  [g]ame reset  [v]iew scores  [w]rite scores  [q]uit")


def computer_take_turn(game: Game, brain) -> None:
    """Computer plays its whole turn (roll until hold or bust)."""
    while True:
        choice = brain.decide(game)
        if choice == "roll":
            value = game.roll()
            print(f"CPU rolled {value}")
            if value == 1:
                print("CPU busted. Your turn.")
                break
            sleep(0.3)  # tiny pause so it doesn't spam
        else:
            game.hold()
            print("CPU holds.")
            break


def play_once(game: Game, sb: Scoreboard, *, mode: str, difficulty: str | None = None) -> None:
    # who are we playing against?
    is_cpu_p2 = (mode == "pvc")

    # pick the bot
    if is_cpu_p2:
        if difficulty == "easy":
            brain = ComputerStrategy(base_threshold=18)
        elif difficulty == "hard":
            brain = SmartStrategy(min_threshold=14, max_threshold=30)
        else:
            brain = SmartStrategy()  # normal
        # name the bot (you can still rename it)
        game.players[1].change_name("Computer")
    else:
        brain = None

    print_header(game)
    print_turn(game, mode, is_cpu_p2)

    while True:
        # winner? record -> reset -> continue
        if game.winner_id is not None:
            sb.record_from_game(game)
            save_scoreboard(sb)
            winner = next(p for p in game.players if p.player_id == game.winner_id)
            print(f"\n🎉 {winner.name} wins with {winner.score}!\n")
            print_recent(sb)
            game.reset(keep_names=True)
            if is_cpu_p2 and game.players[1].name.lower() != "computer":
                game.players[1].change_name("Computer")
            print_header(game)
            print_turn(game, mode, is_cpu_p2)
            continue

        # computer's turn happens before any prompt
        if is_cpu_p2 and game.current is game.players[1]:
            computer_take_turn(game, brain)
            print_turn(game, mode, is_cpu_p2)
            continue

        # human input
        cmd = input("> ").strip().lower()

        if cmd in ("r", "roll"):
            value = game.roll()
            if value == 1:
                print("Rolled 1.")
                print("You BUSTED!")
                print("Score this round: 0 points.")
                print(f"Total score: {game.current.score} points.")
                print(f"{game.current.name}'s turn.")
            else:
                print(f"Rolled {value}. Turn points: {game.turn_points}")

        elif cmd in ("h", "hold"):
            game.hold()
            if game.winner_id is None:
                print(f"Holding. Current Score: {game.opponent.score} points.")
                print(f"{game.current.name}'s turn.")

        elif cmd in ("s", "status"):
            print_header(game)
            print_turn(game, mode, is_cpu_p2)

        elif cmd in ("n", "name", "rename"):
            try:
                who = input("Rename which player? (1/2): ").strip()
                if who not in ("1", "2"):
                    print("Pick 1 or 2.")
                    continue
                new_name = input("New name: ").strip()
                idx = 0 if who == "1" else 1
                game.players[idx].change_name(new_name)
                print_header(game)
                print_turn(game, mode, is_cpu_p2)
            except Exception as e:
                print(f"Name change failed: {e}")

        elif cmd in ("t", "target"):
            try:
                new_target = int(input("New target score: ").strip())
                if new_target < 1:
                    print("Target must be at least 1.")
                    continue
                game.target = new_target
                print(f"Target set to {game.target}.")
            except ValueError:
                print("Please enter a whole number.")

        elif cmd in ("g", "reset", "game"):
            keep = input("Keep player names? (y/n): ").strip().lower() == "y"
            game.reset(keep_names=keep)
            if is_cpu_p2 and game.players[1].name.lower() != "computer":
                game.players[1].change_name("Computer")
            print_header(game)
            print_turn(game, mode, is_cpu_p2)

        elif cmd in ("v", "view", "scoreboard"):
            print_recent(sb)

        elif cmd in ("w", "write", "save"):
            save_scoreboard(sb)
            print(f"Scoreboard saved to {SAVE_PATH.resolve()}")

        elif cmd in ("q", "quit", "exit"):
            save_scoreboard(sb)
            print("Bye!")
            return

        else:
            print("Unknown command. Try: r, h, s, n, t, g, v, w, q")


def print_recent(sb: Scoreboard, n: int = 5) -> None:
    rows = sb.last(n)
    if not rows:
        print("(no games recorded yet)")
        return
    print("\nRecent results:")
    for r in rows:
        scores_str = ", ".join(f"{name}: {pts}" for name, pts in r.scores.items())
        print(f"[{r.when}] to {r.target} — winner: {r.winner} — {scores_str}")
    print()


def choose_mode() -> str:
    while True:
        pick = input("Mode? [1] PvP  [2] PvC: ").strip()
        if pick == "1":
            return "pvp"
        if pick == "2":
            return "pvc"
        print("Choose 1 or 2.")


def choose_difficulty() -> str:
    while True:
        pick = input("Difficulty? [1] Easy  [2] Normal  [3] Hard: ").strip()
        if pick == "1":
            return "easy"
        if pick == "2":
            return "normal"
        if pick == "3":
            return "hard"
        print("Choose 1, 2, or 3.")


def main() -> None:
    game = Game()
    sb = load_scoreboard()

    mode = choose_mode()
    diff = None
    if mode == "pvc":
        diff = choose_difficulty()

    try:
        play_once(game, sb, mode=mode, difficulty=diff)
    except KeyboardInterrupt:
        save_scoreboard(sb)
        print("\nInterrupted. Scoreboard saved. Bye.")


if __name__ == "__main__":
    main()
