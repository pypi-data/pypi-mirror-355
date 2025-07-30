# -*- coding: utf-8 -*-
"""Clases para escribir validadores para entradas y salidas de Karel."""

import collections
import sys
import unittest
import unittest.case
import unittest.suite

from typing import Deque, Set, Union

from . import libkarel


class TestCase(unittest.TestCase):
    """Superclase para definir pruebas de Karel."""
    def setUp(self) -> None:
        super().setUp()

        with open('data.in', 'r') as data_in:
            self.input = self.world = libkarel.KarelInput(data_in.read())
        with open('data.out', 'r') as data_out:
            self.output = libkarel.KarelOutput(data_out.read())
        self.caseName = sys.argv[1]

    def reachableCells(self) -> Set[libkarel.Casilla]:
        """Regresa el conjunto de casillas a las que puede acceder Karel."""
        q: Deque[libkarel.Casilla] = collections.deque(
            ((self.world.x, self.world.y), ))
        visited: Set[libkarel.Casilla] = set()

        while q:
            x, y = q.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            mask = self.world.paredes(x, y)

            if not mask & libkarel.Direccion.NORTE:
                q.append((x, y + 1))
            if not mask & libkarel.Direccion.SUR:
                q.append((x, y - 1))
            if not mask & libkarel.Direccion.ESTE:
                q.append((x + 1, y))
            if not mask & libkarel.Direccion.OESTE:
                q.append((x - 1, y))

        return visited

    def worldBoundaries(self) -> libkarel.Casilla:
        """Regresa una tupla (x, y) con las dimensiones del mundo."""
        x, y = zip(*self.reachableCells())
        return max(x), max(y)

    def assertTightWorldSize(self) -> None:
        """Asevera que las dimensiones del mundo sean correctas.

        Las dimensiones del mundo deben concordar con las casillas
        alcanzables.
        """
        self.assertEqual((self.world.w, self.world.h), self.worldBoundaries())

    def assertNoInnerWalls(self) -> None:
        """Asevera que no haya paredes internas en el mundo."""
        cells = self.reachableCells()

        for x, y in cells:
            w = self.world.paredes(x, y)

            self.assertTrue((x, y + 1) not in cells
                            or (not w & libkarel.Direccion.NORTE))
            self.assertTrue((x, y - 1) not in cells
                            or (not w & libkarel.Direccion.SUR))
            self.assertTrue((x + 1, y) not in cells
                            or (not w & libkarel.Direccion.ESTE))
            self.assertTrue((x - 1, y) not in cells
                            or (not w & libkarel.Direccion.OESTE))


class TestRunner(unittest.TextTestRunner):
    """Un unittest.TestRunner que imprime 1 a salida estándar en éxito."""
    def run(
        self, test: Union[unittest.suite.TestSuite, unittest.case.TestCase]
    ) -> unittest.TextTestResult:
        result = super().run(test)
        if result is not None and result.wasSuccessful():
            print(1)
        else:
            print(0)
        return result


def main() -> None:
    """Ejecuta las pruebas del archivo actual."""
    unittest.main(testRunner=TestRunner, argv=[sys.argv[0], '-v'])
