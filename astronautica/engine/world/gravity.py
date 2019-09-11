from astropy import units as u

from ..abc import Domain, Node


class Orbit(object):
    def __init__(self, master: Domain, slave: Node):
        self.master: Domain = master
        self.slave: Node = slave


class MultiSystem(set, Domain):
    """Representation of a Gravitational System without any clear "Master".
        Typically the case for Stars near each other.
    """

    def __init__(self, *bodies: Domain):
        if len(bodies) < 2:
            raise ValueError("A Multi System must have at least two Objects.")

        super().__init__(bodies)
        # self.slaves: Tuple[Node, ...] = bodies

    @property
    def mass(self):
        return sum((o.mass for o in self), u.kg * 0)

    @property
    def units(self):
        return tuple(self)[0].units

    def serialize(self):
        return dict(
            type=type(self).__name__,
            subs=dict(bodies=list(filter(None, (o.serialize() for o in self)))),
        )

    @classmethod
    def from_serial(cls, data, subs):
        return cls(*subs["bodies"])


class System(set, Domain):
    """Representation of a Gravitational System with a clear "Master". Typically
        the case for Planetary Systems orbiting a single Star.
    """

    def __init__(self, master: Domain, *slaves: Domain):
        self.master: Domain = master

        super().__init__(slaves)
        # self.slaves: Set[Node] = {*slaves}

    @property
    def mass(self):
        return sum((o.mass for o in self), self.master.mass)

    @property
    def units(self):
        return self.master.units

    def serialize(self):
        return dict(
            type=type(self).__name__,
            subs=dict(
                master=self.master.serialize(),
                slaves=list(filter(None, (o.serialize() for o in self))),
            ),
        )

    @classmethod
    def from_serial(cls, data, subs):
        return cls(subs["master"], *subs["slaves"])