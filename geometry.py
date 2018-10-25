import math

from astropy import units as u
import numpy as np

# CONSTANT DIRECTIONS
# (θ elevation, φ azimuth)
NORTH = (0 * u.degree, 0 * u.degree)
EAST = (0 * u.degree, 90 * u.degree)
WEST = (0 * u.degree, -90 * u.degree)
SOUTH = (0 * u.degree, 180 * u.degree)

ZENITH = (90 * u.degree, 0 * u.degree)
NADIR = (-90 * u.degree, 0 * u.degree)


def npr(n):
    return np.round(n, 5)


def rad_deg(theta):
    return npr(math.degrees(theta))
    # return np.round(theta * 57.2958, Precision)


def deg_rad(theta):
    return npr(math.radians(theta))


def cart2_polar2(x, y):
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.pi / 2 - np.arctan2(y, x)
    return rho, phi


def polar2_cart2(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y


def cart3_polar3(x, y, z):
    rho = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    phi = rad_deg(np.arccos(z / rho))
    theta = rad_deg(np.arctan(y / x))
    return npr((rho, theta, phi))


def polar3_cart3(rho, theta, phi):
    theta = np.pi / 2 - deg_rad(theta)
    phi = deg_rad(phi)
    x = rho * np.sin(phi) * np.sin(theta)
    y = rho * np.cos(theta)
    z = rho * np.cos(phi) * np.sin(theta)
    return npr((x, y, z))


class Coordinates:
    """Coordinates object:
    Store coordinates as a cartesian tuple and return transformations as requested"""

    def __init__(self, *, car=None, cyl=None, pol=None, heading=None, course=None):
        if car and len(car) >= 3:  # CARTESIAN: (X, Y, Z)
            self.cartesian = (car[0], car[1], car[2])
        elif cyl and len(cyl) >= 3:  # CYLINDRICAL: (R, φ azimuth, Y)
            y = cyl[2]
            z, x = polar2_cart2(cyl[0], deg_rad(cyl[1]))
            self.cartesian = (x, y, z)
        elif pol and len(pol) >= 3:  # SPHERICAL: (R, θ elevation, φ azimuth)
            self.cartesian = polar3_cart3(*pol)
        else:
            raise TypeError("Coordinates object requires initial values")

        self.heading = heading or (
            0,
            0,
            0,
        )  # (pitch, yaw, roll); FACING orientation of object
        self.course = course or (
            0,
            0,
        )  # (θ elevation, φ azimuth); Direction object is MOVING
        self.velocity = 0 #* (u.meter / u.second)
        # Velocity can be considered the rho of the course

    @property
    def array(self):
        return np.array(
            [
                self.cartesian,
                self.heading,
                self.course + (self.velocity,)
            ]
        )
        # return np.array(
        #     [
        #         [*self.cartesian] * u.kilometer,
        #         [*self.heading] * u.degree,
        #         [*self.course] * u.degree,
        #         self.velocity
        #     ]
        # )

    @property
    def c_car(self):
        """Return the CARTESIAN coordinates"""
        return np.array([npr(v) for v in self.cartesian])

    @property
    def c_cyl(self):
        """Return the CYLINDRICAL coordinates"""
        x, y, z = self.cartesian  # Take the cartesian coordinates
        rho, phi = cart2_polar2(x, z)  # Find rho and phi of x and z
        return np.array((npr(rho), rad_deg(phi), npr(y)))  # Return rho, phi, and height

    @property
    def c_pol(self):
        """Return the SPHERICAL coordinates (horizontal)"""
        x, y, z = self.cartesian
        return cart3_polar3(x, y, z)
        # rho0, phi = cart2_polar2(x, y)
        # rho, theta = cart2_polar2(z, rho0)
        # return rho, theta, phi


def get_bearing(a, b):
    """Return SPHERICAL coordinates (horizontal) of relative position"""
    ap = a.c_pol  # Polar of A
    ac = a.c_car  # Cartesian of A
    bp = b.c_pol  # Polar of B
    bc = b.c_car  # Cartesian of B
    ab_r = np.sqrt(
        (ac[0] - bc[0]) ** 2 + (ac[1] - bc[1]) ** 2 + (ac[2] - bc[2]) ** 2
    )  # Rho of output
    ab_tp = ap[1] - bp[1], ap[2] - bp[2]  # Theta and Phi of output
    ab = ab_r, *ab_tp
    return ab


def get_cylinder(a, b):
    bearing = get_bearing(a, b)


# def get_relative(a, b):
#     """Return CYLINDRICAL coordinates of relative position"""
#     pass
