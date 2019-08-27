"""Module dedicated to calculating Collision Detection between Objects.

Uses Numba for JIT Compilation.
"""

from typing import Tuple

from numba import jit
import numpy as np
from vectormath import Vector3


@jit(nopython=True)
def get_delta_v(
    e: float,
    normal: np.ndarray,
    velocity_a: np.ndarray,
    velocity_b: np.ndarray,
    mass_a: float,
    mass_b: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Given a Coefficient, a Normal, and the Velocities and Masses of two
        Objects, return the Δv values of a collision between the Objects. The
        first and second returned Vectors should be added to the Velocities of
        the first and second Objects, respectively.

    This equation is not complete, as I have purposefully left out rotation, at
        least for the time being.

    https://www.euclideanspace.com/physics/dynamics/collision/threed/index.htm
        J = -(1+e) * (
            ((vai-vbi) • n)
            /
            (1/ma + 1/mb)
        )
        vaf = vai + (J / ma)
        vbf = vbi - (J / mb)
    """
    J: np.ndarray = normal * (
        -(1 + e)
        * (np.dot((velocity_a - velocity_b), normal) / ((1 / mass_a) + (1 / mass_b)))
    )
    return J / mass_a, -J / mass_b


@jit(looplift=True, nopython=True)
def _find(
    pos_a: Vector3,
    vel_a: Vector3,
    pos_b: Vector3,
    vel_b: Vector3,
    time_min: float,
    time_max: float,
    contact: float,
):
    result = 0
    error = 0
    # graph = {}

    def distance_at(time):
        a = pos_a + vel_a * time
        b = pos_b + vel_b * time
        return float(np.sqrt(np.sum(np.square(a - b))))

    dist_min: float = distance_at(time_min)
    dist_max: float = distance_at(time_max)

    # graph[time_min] = dist_min
    # graph[time_max] = dist_max

    i = 0
    while contact - error > 0.001 and i < 100:
        # Repeat the following over an increasingly precise window of time.
        time_mid = (time_min + time_max) / 2
        dist_mid = distance_at(time_mid)
        i += 1

        # graph[time_mid] = dist_mid

        if dist_min < contact:
            # The objects are in contact at the start of this window.
            result = False
            break

        elif dist_mid < contact:
            # The objects are in contact halfway through this window.
            result = time_mid
            error = dist_mid
            time_max = time_mid
            dist_max = dist_mid

        elif dist_max < contact:
            # The objects are in contact at the end of this window.
            result = time_max
            error = dist_max
            time_min = time_mid
            dist_min = dist_mid

        else:
            # The objects are not in contact at any known point; However, they
            #   may still pass through each other between points. Check the
            #   distance differences to find which half of this window would
            #   contain the pass.
            half_0 = dist_mid - dist_min  # Change in distance over the first half
            half_1 = dist_max - dist_mid  # Change in distance over the second half

            if dist_min < dist_mid < dist_max:
                # The objects seem to be diverging, but may have passed.

                if half_0 == half_1:
                    # Divergence is constant; Objects do not pass.
                    result = False
                    break

                elif half_0 > half_1:
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half.
                    time_min = time_mid
                    dist_min = dist_mid

                else:  # half_0 < half_1
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half.
                    time_max = time_mid
                    dist_max = dist_mid

            elif dist_min > dist_mid > dist_max or (
                dist_min > dist_mid and dist_max > dist_mid
            ):
                # The objects seem to be converging, or to have passed.

                if half_0 == half_1:
                    # Convergence is constant; Objects have not passed yet.
                    result = False
                    break

                elif half_0 < half_1:
                    # First half is smaller change than second half;
                    # If they pass, it happens in the first half.
                    time_min = time_mid
                    dist_min = dist_mid

                else:  # half_0 > half_1
                    # First half is greater change than second half;
                    # If they pass, it happens in the second half.
                    time_max = time_mid
                    dist_max = dist_mid

            else:
                # No other condition could result in an impact
                result = False
                break

    # print(repr({k: graph[k] for k in sorted(graph.keys())}))
    return result


@jit(forceobj=True, nopython=False)
def find_collision(obj_a, obj_b, end: float, start: float = 0.0):
    """Iteratively zero in on the first time where the distance between two
        objects is less than the sum of their radii. Return a float of seconds
        at which the objects collide, or False if they do not.
    """
    contact = obj_a.radius + obj_b.radius

    pos_a = obj_a.coords.position
    vel_a = obj_a.coords.velocity
    pos_b = obj_b.coords.position
    vel_b = obj_b.coords.velocity

    return _find(pos_a, vel_a, pos_b, vel_b, start, end, contact)


# Implementation by Fnord on StackOverflow
# https://stackoverflow.com/a/18994296


@jit(forceobj=True, nopython=False)
def distance_between_lines(
    a0: np.ndarray,
    a1: np.ndarray,
    b0: np.ndarray,
    b1: np.ndarray,
    clampAll: bool = True,
    clampA0: bool = False,
    clampA1: bool = False,
    clampB0: bool = False,
    clampB1: bool = False,
):
    """ Given two lines defined by numpy.array pairs (a0,a1,b0,b1)
        Return the closest points on each segment and their distance
    """

    # If clampAll=True, set all clamps to True
    if clampAll:
        clampA0 = True
        clampA1 = True
        clampB0 = True
        clampB1 = True

    # Calculate denomitator
    A = np.subtract(a1, a0)
    B = np.subtract(b1, b0)
    magA = np.linalg.norm(A)
    magB = np.linalg.norm(B)

    # print(f"\n\n{A} / {magA}; {B} / {magB}")
    _A = np.true_divide(A, magA) if magA != 0 else A
    _B = np.true_divide(B, magB) if magB != 0 else B
    # print(f"{_A}, {_B}")

    cross = np.cross(_A, _B)
    denom = np.square(np.linalg.norm(cross))

    # If lines are parallel (denom=0) test if lines overlap.
    # If they don't overlap then there is a closest point solution.
    # If they do overlap, there are infinite closest positions, but there is a closest distance
    if not denom:
        d0 = np.dot(_A, (b0 - a0))

        # Overlap only possible with clamping
        if clampA0 or clampA1 or clampB0 or clampB1:
            d1 = np.dot(_A, (b1 - a0))

            # Is segment B before A?
            if d0 <= 0 >= d1:
                if clampA0 and clampB1:
                    if np.absolute(d0) < np.absolute(d1):
                        return a0, b0, np.linalg.norm(a0 - b0)
                    return a0, b1, np.linalg.norm(a0 - b1)

            # Is segment B after A?
            elif d0 >= magA <= d1:
                if clampA1 and clampB0:
                    if np.absolute(d0) < np.absolute(d1):
                        return a1, b0, np.linalg.norm(a1 - b0)
                    return a1, b1, np.linalg.norm(a1 - b1)

        # Segments overlap, return distance between parallel segments
        return None, None, np.linalg.norm(((d0 * _A) + a0) - b0)

    # Lines criss-cross: Calculate the projected closest points
    t = np.subtract(b0, a0)

    # print(f"\n\ndetA = det({[t, _B, cross]}); detB = det({[t, _A, cross]})")
    detA = np.linalg.det([t, _B, cross])
    detB = np.linalg.det([t, _A, cross])
    # print(f"{detA}, {detB}")

    t0 = detA / denom
    t1 = detB / denom

    pA = a0 + (_A * t0)  # Projected closest point on segment A
    pB = b0 + (_B * t1)  # Projected closest point on segment B

    # Clamp projections
    if clampA0 or clampA1 or clampB0 or clampB1:
        if clampA0 and t0 < 0:
            pA = a0
        elif clampA1 and t0 > magA:
            pA = a1

        if clampB0 and t1 < 0:
            pB = b0
        elif clampB1 and t1 > magB:
            pB = b1

        # Clamp projection A
        if (clampA0 and t0 < 0) or (clampA1 and t0 > magA):
            dot = np.dot(_B, (pA - b0))
            if clampB0 and dot < 0:
                dot = 0
            elif clampB1 and dot > magB:
                dot = magB
            pB = b0 + (_B * dot)

        # Clamp projection B
        if (clampB0 and t1 < 0) or (clampB1 and t1 > magB):
            dot = np.dot(_A, (pB - a0))
            if clampA0 and dot < 0:
                dot = 0
            elif clampA1 and dot > magA:
                dot = magA
            pA = a0 + (_A * dot)

    return pA, pB, np.linalg.norm(pA - pB)
