"""cmd-based terminal shell for the Pig game."""
from __future__ import annotations
import cmd
import json
from pathlib import Path
from time import sleep

from pig.game import Game
from pig.scoreboard import Scoreboard
from pig.ai import ComputerStrategy, SmartStrategy
from pig.cheat import Cheat


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


def _build_brain(difficulty: str):
    if difficulty == "easy":
        return ComputerStrategy(base_threshold=18)
    if difficulty == "hard":
        return SmartStrategy(min_threshold=14, max_threshold=30)
    return SmartStrategy()  # normal


class PigShell(cmd.Cmd):
    intro = "Pig — type 'help' for commands. Start with 'status' or 'roll'."
    prompt = "> "

    def __init__(self, game: Game, sb: Scoreboard) -> None:
        super().__init__()
        self.game = game
        self.sb = sb
        self.mode = "pvp"
        self.difficulty = "normal"
        self.brain = None          
        self._cheat = Cheat(self.game)   # stays dormant until armed
        self._cheat_unlocked = False
        self._cheat_word = "pepper"      # change this to whatever you like

        #self._print_header()

    def _print_header(self) -> None:
        g = self.game
        print("=" * 42)
        print(f"Pig — first to {g.target} wins")
        print("-" * 42)
        p1, p2 = g.players
        print(f"{p1.name:>12}: {p1.score:>3}   vs   {p2.name:<12}: {p2.score:>3}")
        print("-" * 42)
        self._print_turn()

    def _print_turn(self) -> None:
        g = self.game
        print(f"Current: {g.current.name}")
        print(f"Turn points: {g.turn_points}")
        if self.mode == "pvc" and self.brain and g.current is g.players[1]:
            print("Computer is thinking…")

    def _ensure_cpu_name(self) -> None:
        """Rename Player 2 to 'Computer' only if we're in PvC and it's still the default name."""
        if self.mode == "pvc" and self.game.players[1].name == "Player 2":
            self.game.players[1].change_name("Computer")

    def _maybe_record_winner(self) -> None:
        if self.game.is_over:
            winner = self.game.get_winner()
            self.sb.record_from_game(self.game)
            save_scoreboard(self.sb)
            print(f"\n🎉 {winner.name} wins with {winner.score}!\n")
            self._print_recent()
            self.game.reset(keep_names=True)
            self._ensure_cpu_name()
            self._print_header()

    def _cpu_take_turn(self) -> None:
        """Run the computer's whole turn (no prompts)."""
        if self.mode != "pvc" or not self.brain:
            return
        if self.game.current is not self.game.players[1]:
            return

        result = self.game.play_cpu_turn(self.brain.decide)
        for step in result.get("actions", []):
            if step["action"] == "roll":
                print(f"{self.game.players[1].name} rolled {step['value']}")
                if step["value"] == 1:
                    print("CPU busted.")
                    print(f"{self.game.current.name}'s turn.")
                    break
                sleep(0.25)
        if result["ended"] == "hold":
            print("CPU holds.")
            print(f"CPU score: {self.game.players[1].score} points.")
            print(f"{self.game.current.name}'s turn.")

    def _print_recent(self, n: int = 5) -> None:
        rows = self.sb.last(n)
        if not rows:
            print("(no games recorded yet)")
            return
        print("Recent results:")
        for r in rows:
            line = ", ".join(f"{name}: {pts}" for name, pts in r.scores.items())
            print(f"[{r.when}] to {r.target} — winner: {r.winner} — {line}")
        print()

    def _prompt_mode_and_diff(self) -> None:
        """Ask once at startup: PvP or PvC (and difficulty)."""
        while True:
            pick = input("Mode? [1] PvP  [2] PvC: ").strip()
            if pick in {"1", "2"}:
                break
            print("Choose 1 or 2.")
        self.mode = "pvc" if pick == "2" else "pvp"

        if self.mode == "pvc":
            while True:
                d = input("Difficulty? [1] Easy  [2] Normal  [3] Hard: ").strip()
                if d in {"1", "2", "3"}:
                    break
                print("Choose 1, 2, or 3.")
            self.difficulty = {"1": "easy", "2": "normal", "3": "hard"}[d]
            self.brain = _build_brain(self.difficulty)
            self._ensure_cpu_name()

        print(f"Mode set to {self.mode}" + (f" ({self.difficulty})" if self.mode == "pvc" else ""))

    def preloop(self):
        self._prompt_mode_and_diff()
        self._print_header()

    def postcmd(self, stop: bool, line: str) -> bool:
        # After every command, check winner, then let CPU act if it's their turn
        self._maybe_record_winner()
        self._cpu_take_turn()
        self._maybe_record_winner()
        return stop

    def do_roll(self, arg):
        """roll: Roll the dice for the current player."""
        v = self.game.roll()
        if v == 1:
            print("Rolled 1.")
            sleep(0.25)
            print("BUSTED! No points this turn.")
            sleep(0.25)
            print("Score this round: 0 points.")
            sleep(0.25)
            print(f"Total score: {self.game.current.score} points.")
            sleep(0.25)
            print(f"{self.game.current.name}'s turn.")
            sleep(0.25)
        else:
            print(f"Rolled {v}. Turn points: {self.game.turn_points}")

    def do_hold(self, arg):
        """hold: Bank current turn points."""
        self.game.hold()
        if not self.game.is_over:
            print(f"Holding. Current Score: {self.game.opponent.score} points.")
            sleep(0.25)
            print(f"{self.game.current.name}'s turn.")
            sleep(0.25)

    def do_status(self, arg):
        """status: Show scores and whose turn it is."""
        self._print_header()

    def do_name(self, arg):
        """name <1|2> <new name>: Rename a player."""
        try:
            idx_str, *rest = arg.split()
            if idx_str not in ("1", "2") or not rest:
                print("Usage: name 1 Alice")
                return
            new_name = " ".join(rest)
            self.game.rename(int(idx_str), new_name)
            self._print_header()
        except Exception as e:
            print(f"Name change failed: {e}")

    def do_target(self, arg):
        """target <points>: Set new target score (>= 1)."""
        try:
            self.game.set_target(int(arg.strip()))
            print(f"Target set to {self.game.target}.")
        except Exception as e:
            print(f"Could not set target: {e}")

    def do_reset(self, arg):
        """reset [keep|clear]: Reset the game. Keep names by default."""
        keep = (arg.strip().lower() != "clear")
        self.game.reset(keep_names=keep)
        self._ensure_cpu_name()
        self._print_header()

    def do_view(self, arg):
        """view: Show recent scoreboard results."""
        self._print_recent()

    def do_save(self, arg):
        """save: Write scoreboard to disk."""
        save_scoreboard(self.sb)
        print(f"Scoreboard saved to {SAVE_PATH.resolve()}")

    # ----- mode / difficulty ------------------------------------------

    def do_mode(self, arg):
        """mode <pvp|pvc>: Switch between two humans or vs computer."""
        val = arg.strip().lower()
        if val not in {"pvp", "pvc"}:
            print("Pick 'pvp' or 'pvc'.")
            return
        self.mode = val
        self.brain = _build_brain(self.difficulty) if self.mode == "pvc" else None
        self._ensure_cpu_name()
        self._print_header()

    def do_diff(self, arg):
        """diff <easy|normal|hard>: Set computer difficulty (PvC only)."""
        val = arg.strip().lower()
        if val not in {"easy", "normal", "hard"}:
            print("Pick 'easy', 'normal' or 'hard'.")
            return
        self.difficulty = val
        if self.mode == "pvc":
            self.brain = _build_brain(self.difficulty)
        print(f"Difficulty set to {self.difficulty}.")

    def do_quit(self, arg):
        """quit: Exit the game."""
        save_scoreboard(self.sb)
        print("Bye!")
        return True

    def do_EOF(self, arg):
        """Ctrl+D/Ctrl+Z: Exit."""
        print()
        return self.do_quit(arg)

    def default(self, line: str) -> bool:
    # if user types the magic word, open the cheat menu
        if line.strip().lower() == self._cheat_word:
            self._cheat.arm()
            self._cheat_unlocked = True
            print("(dev) cheats unlocked.")
            self._cheat_menu()
            return False
    # otherwise, just say we don't know that command
        print(f"Unknown command: {line!r}. Type 'help' for a list of commands.")
        return False
    
    def _cheat_menu(self) -> None:
        if not self._cheat_unlocked:
            print("nope.")
            return

        print("\ncheat menu — type 'back' to exit")
        print("  next <vals...>     # force next rolls, e.g. 'next 6 6 2'")
        print("  nobust on|off      # 1s count as 2 when on")
        print("  add <p> <pts>      # add points to player 1/2")
        print("  score <p> <n>      # set exact score for player 1/2")
        print("  win [p]            # make player 1 (or 2) win now")
        print("  clear              # clear all cheat knobs\n")

        while True:
            cmd = input("(cheat)> ").strip().lower()
            if cmd in {"back", "exit", "quit"}:
                print("leaving cheat menu.\n")
                return
            if not cmd:
                continue

            parts = cmd.split()
            op = parts[0]
            try:
                if op == "next":
                    for v in parts[1:]:
                        self._cheat.force_next_roll(int(v))
                    print("ok.")
                elif op == "nobust":
                    on = len(parts) > 1 and parts[1] == "on"
                    self._cheat.no_bust_on_ones(on)
                    print(f"nobust {'on' if on else 'off'}.")
                elif op == "add":
                    p, pts = int(parts[1]), int(parts[2])
                    self._cheat.add_points(p, pts)
                    print("ok.")
                elif op == "score":
                    p, n = int(parts[1]), int(parts[2])
                    self._cheat.set_score(p, n)
                    print("ok.")
                elif op == "win":
                    p = int(parts[1]) if len(parts) > 1 else 1
                    self._cheat.win_now(p)
                    print("ok.")
                elif op == "clear":
                    self._cheat.clear()
                    print("cleared.")
                else:
                    print("huh?")
            except Exception as e:
                print(f"err: {e}")