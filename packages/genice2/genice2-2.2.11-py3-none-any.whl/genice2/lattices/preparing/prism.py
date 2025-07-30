# coding: utf-8
"""
Generate a hydrogen-disordered prism ice. (Cylindrical ice)

Usage:
    genice2 prism       A prism of default sides and rows (6,10)
    genice2 prism[5]    A pentagonal prism of 10 rows.
    genice2 prism[8,6]  An octagonal prism of 6 rows.

Options:
    [sides[,rows]]    Number of sides and rows.

"""

import genice2.lattices
from genice2.cell import cellvectors
from logging import getLogger
from math import sin, pi, cos


def usage():
    logger = getLogger()
    logger.info(__doc__)


desc = {
    "ref": {
        "prism": "Koga 2001"
    },
    "usage": usage(),
    "brief": "Ice nanotubes."
}


class Lattice(genice2.lattices.Lattice):
    """
Generate a prism ice.

Options:
  rows=r
  sides=s
    """

    def __init__(self, **kwargs):
        logger = getLogger()
        # global sides, rows, bondlen, density, cell, waters, coord
        sides = 6
        rows = 10

        for k, v in kwargs.items():
            if k == "rows":
                rows = int(v)
            elif k == "sides":
                sides = int(v)
            elif v is True:
                # unlabeled option
                values = k.split(",")
                if len(values) == 2:
                    sides, rows = [int(x) for x in values]
                elif len(values) == 1:
                    sides = int(values[0])
                else:
                    sys.exit(1)

        logger.info(
            "Prism ice with {0} sides and {1} rows.".format(sides, rows))

        L = 2.75
        self.bondlen = 3
        R = L / 2 / sin(pi / sides)
        self.density = sides * rows / \
            (L**3 * 400 * rows) * 18 / 6.022e23 * 1e24

        self.waters = []
        for j in range(rows):
            for i in range(sides):
                x = R * cos(i * pi * 2 / sides)
                y = R * sin(i * pi * 2 / sides)
                z = j * L
                self.waters.append([x, y, z])

        self.coord = "absolute"

        self.cell = cellvectors(a=L * 20,
                                b=L * 20,
                                c=L * rows)
