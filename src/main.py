# """Entry point for the Pig game project."""
# from pig.shell import main

# if __name__ == "__main__":
#     main()

"""Entry point for the Pig game project (cmd-based)."""
from pig.shell import PigShell, load_scoreboard
from pig.game import Game

def main() -> None:
    shell = PigShell(Game(), load_scoreboard())
    shell.cmdloop()

if __name__ == "__main__":
    PigShell().cmdloop()
