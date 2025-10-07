from cmd import Cmd
from pig.dice import Dice


class PigShell(Cmd):
    """
    A minimal command-line shell for testing the Pig game.
    """

    intro = "Welcome to Pig Game (prototype)! Type help or ? to list commands."
    prompt = "(pig) "

    def do_roll(self, arg):
        """Roll a six-sided dice. Usage: roll"""
        d = Dice()
        print(f"You rolled: {d.roll()}")

    def do_rules(self, arg):
        """Show placeholder rules. Usage: rules"""
        print("Rules: This is just a placeholder. Full Pig rules will come later.")

    def do_quit(self, arg):
        """Quit the game. Usage: quit"""
        print("Bye!")
        return True

    # Alias for quit
    do_exit = do_quit

    def emptyline(self):
        """Prevent repeating the last command on empty line."""
        pass


if __name__ == "__main__":
    PigShell().cmdloop()
