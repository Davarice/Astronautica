print("Connection established. Initiating QES 3.1 key exchange...")

from pathlib import Path

from .core import TerminalCore, _delay, _interruptible
from .game import TerminalHost
from .ship import TerminalShip
from astronautica import config
from astronautica.util import paths


class TerminalLogin(TerminalCore):
    """
    The login shell. A game lobby of sorts, from which the user launches the other shells.
    """

    host_init = "FleetNet"
    intro = "Secure connection to FleetNet complete. For help: 'help' or '?'"
    farewell = "QLink powering down..."
    promptColor = "\033[33m"

    def __init__(self):
        super().__init__()
        self.path = "/"
        self.game = None

    def do_ls(self, line):
        """List currently active Host Stations, or vessels in range of a Host Station.
        Syntax: ls [<host_name>]"""
        if line:
            path = Path(config.working_dir, line)
            title = "List of vessels in range of Host '{}':".format(line)
        else:
            path = Path(config.working_dir)
            title = "List of live Host Stations:"
        ls = [p.stem for p in path.glob("*")]
        if not path.is_dir() or not ls:
            print("Nothing found.")
            return
        print(title)
        for host in ls:
            if not host.endswith("_orders"):
                print("  - " + host)

    def do_host(self, line):
        """Tunnel to a Host Station through which interacting constructs can be directed.
        Syntax: host <host_name>"""
        if self.game:
            if line:
                print("Another connection from this terminal is already open.")
            else:
                self.game.cmdloop()
        else:
            name = (line or input("Enter title of Host Station: ")).strip()
            if not name:
                print("Invalid name.")
            elif (paths.root / name).exists():
                print("Duplicate name.")
            else:
                self.game = TerminalHost(name)
                self.game.cmdloop()
        if self.game.killed:
            self.game = None

    @_interruptible
    def do_login(self, line):
        """Connect to a vessel via QSH to check its scans or issue orders.
        Syntax: login <host_name>/<vessel_name>"""
        name = (line or input("Enter 'host/vessel': ")).strip()
        if not name or name.count("/") != 1:
            print("Invalid name.")
            return

        host, vessel = name.split("/")
        hostpath = Path(config.working_dir, host)
        shippath = hostpath.joinpath(vessel)
        if not hostpath.resolve().is_dir():
            print("Host Station not found.")
            return
        elif not shippath.with_suffix(".json").resolve().is_file():
            print("Vessel not found.")
            return

        print(
            "Connecting to qsh://FleetNet.{}:{} as '{}'...".format(
                host, vessel, self.user
            )
        )
        shell = TerminalShip(hostpath, shippath)
        if shell.authenticate():
            shell.cmdloop()

    def do_exit(self, *_):
        if self.game:
            return self.game.do_kill()
        else:
            return super().do_exit()
