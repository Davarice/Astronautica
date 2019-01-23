from cmd import Cmd
from getpass import getuser
from random import randint
from time import sleep

_PromptString = "{c}{u}@{h}\033[0m:\033[94m{p}\033[0m$ "
_aliases = {"quit": "exit", "logout": "exit"}


def _delay(a=5, b=20):
    """Wait a short time to simulate an advanced function that causes a hang"""
    sleep(randint(a, b) / 10)


def _interruptible(func):
    """Designates a method during which a KeyboardInterrupt will not exit the shell."""

    def attempt(*a, **kw):
        try:
            func(*a, **kw)
        except EOFError:
            print("(Interrupted)")
        except KeyboardInterrupt:
            print("(Interrupted)")

    attempt.__doc__ = func.__doc__
    return attempt


class TerminalCore(Cmd):
    """
    The core shell, implementing functionality shared by all three primaries.
    Also wraps the cmdloop method as an interruptible, allowing smoother exiting via ^C.
    """

    prompt_init = "Offline"
    intro = None
    farewell = None
    promptColor = "\033[93m"

    def __init__(self):
        super().__init__()
        self.host = self.prompt_init
        self.path = "/"

    @property
    def user(self):
        return getuser()

    @property
    def prompt(self):
        return _PromptString.format(
            c=self.promptColor, u=self.user.lower(), h=self.host, p=self.path
        )

    @_interruptible
    def cmdloop(self, *a, **kw):
        return super().cmdloop(*a, **kw)

    def do_exit(self, *_):
        """Exit this context and return to the above shell."""
        if self.farewell:
            print(self.farewell)
        return True

    def default(self, line):
        if line.lower() in ["credits", "source"]:
            print(
                "Astronautica by @Davarice, licensed under GPLv3\n"
                + "https://github.com/Davarice/Astronautica"
            )
            return
        ls = line.split(" ", 1)
        cmd, rest = ls.pop(0), ls if ls else ""
        if cmd in _aliases and getattr(self, "do_" + _aliases[cmd], False):
            return self.onecmd(" ".join([_aliases[cmd], rest]))
        if line == "EOF":
            print("exit")
            return self.do_exit(line)
        else:
            return super().default(line)