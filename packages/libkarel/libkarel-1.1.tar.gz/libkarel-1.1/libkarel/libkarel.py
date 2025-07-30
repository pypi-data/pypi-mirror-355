# -*- coding: utf-8 -*-
"""Librería para parsear entradas y salidas de Karel en XML."""

import enum
import collections
import sys
import xml.etree.ElementTree as ET

from typing import (DefaultDict, Dict, List, NamedTuple, Optional, Set, Tuple,
                    Union)

Casilla = Tuple[int, int]
Cantidad = Union[int, str]  # Un número o la cadena 'INFINITO'


def _cantidad(c: str) -> Cantidad:
    if c == 'INFINITO':
        return c
    return int(c)


class Zumbadores(NamedTuple):
    """Información sobre los zumbadores de una casilla."""
    x: int
    y: int
    zumbadores: Cantidad


class Direccion(enum.IntFlag):
    """Constantes para las máscara de bits de las paredes del mundo"""
    OESTE = 1
    NORTE = 2
    ESTE = 4
    SUR = 8


class KarelInput:
    """Representa un archivo .in."""
    def __init__(self, contents: str):
        # pylint: disable=too-many-statements
        self.root = ET.fromstring(contents)
        self.__version = str(self.root.attrib.get('version', '1.0'))
        mundo = self.root.find('mundos/mundo')
        if mundo is not None:
            self.__w = int(mundo.attrib['ancho'])
            self.__h = int(mundo.attrib['alto'])
        else:
            self.__w = 100
            self.__h = 100

        condiciones = self.root.find('condiciones')
        if condiciones is not None:
            self.__instrucciones_maximas = int(
                condiciones.attrib['instruccionesMaximasAEjecutar'])
            self.__longitud_stack = int(condiciones.attrib['longitudStack'])
            self.__memoria_stack = int(
                condiciones.attrib.get('memoriaStack', 0))
            self.__llamada_maxima = int(
                condiciones.attrib.get('llamadaMaxima', 0))
        else:
            self.__instrucciones_maximas = 0
            self.__longitud_stack = 0
            self.__memoria_stack = 0
            self.__llamada_maxima = 0

        self.__limites = {
            x.attrib['nombre']: int(x.attrib['maximoNumeroDeEjecuciones'])
            for x in self.root.findall('condiciones/comando')
        }

        programa = self.root.find('programas/programa')
        self.__mochila: Cantidad = 'INFINITO'
        if programa is not None:
            self.__x = int(programa.attrib['xKarel'])
            self.__y = int(programa.attrib['yKarel'])
            self.__direccion = programa.attrib['direccionKarel']
            self.__mochila = _cantidad(programa.attrib['mochilaKarel'])
        else:
            self.__x = 1
            self.__y = 1
            self.__direccion = 'NORTE'

        self.__despliega = [
            x.attrib['tipo'].upper()
            for x in self.root.findall('programas/programa/despliega')
        ]
        self.__despliega_orientacion = 'ORIENTACION' in self.despliega
        self.__despliega_mundo = 'MUNDO' in self.despliega
        self.__despliega_posicion = 'POSICION' in self.despliega
        self.__despliega_instrucciones = 'INSTRUCCIONES' in self.despliega

        lista_zumbadores = [
            Zumbadores(
                x=int(x.attrib['x']),
                y=int(x.attrib['y']),
                zumbadores=_cantidad(x.attrib['zumbadores']),
            ) for x in self.root.findall('mundos/mundo/monton')
        ]
        self.__zumbadores = {(x.x, x.y): x.zumbadores
                             for x in lista_zumbadores}

        lista_dump = [{k: int(x.attrib[k])
                       for k in x.attrib}
                      for x in self.root.findall('mundos/mundo/posicionDump')]
        self.__dump = set((x['x'], x['y']) for x in lista_dump)

        self.__paredes: DefaultDict[
            Casilla, Direccion] = collections.defaultdict(lambda: Direccion(0))

        # Las paredes se representan como el segmento que une dos puntos
        # (x1,y1), (x2,y2) en el plano.
        #
        # Pensemos en el caso de una pared horizontal. Sin pérdida de
        # generalidad, sea x1 > x2. El diagrama ilustra este caso:
        #
        #        pared
        #          |
        # (x2, y2) v (x1, y1)
        #    * --------- *
        #    |           |
        #    |           |
        #    |  (x1, y1) <- celda con una pared al norte
        #    |           |
        #    |           |
        #    * - - - - - *
        #
        # El código asigna x = max(x1, x2), y = y1 = y2.  Eso basta para saber
        # cuáles son las dos celdas adyacentes a la pared. El caso vertical es
        # análogo.
        #
        # En el XML se distingue del caso vertical u horizontal por la
        # existencia o no de los atributos x2, y2, ya que se obvia el que está
        # repetido.
        for x in range(1, self.__w + 1):
            self.__paredes[(x, 0)] |= Direccion.NORTE
            self.__paredes[(x, 1)] |= Direccion.SUR
            self.__paredes[(x, self.__h)] |= Direccion.NORTE
            self.__paredes[(x, self.__h + 1)] |= Direccion.SUR

        for y in range(1, self.__h + 1):
            self.__paredes[(0, y)] |= Direccion.ESTE
            self.__paredes[(1, y)] |= Direccion.OESTE
            self.__paredes[(self.__w, y)] |= Direccion.ESTE
            self.__paredes[(self.__w + 1, y)] |= Direccion.OESTE

        for pared in self.root.findall('mundos/mundo/pared'):
            x = int(pared.attrib['x1'])
            y = int(pared.attrib['y1'])

            if 'x2' in pared.attrib:
                x = max(x, int(pared.attrib['x2']))
                self.__paredes[(x, y)] |= Direccion.NORTE
                self.__paredes[(x, y + 1)] |= Direccion.SUR
            elif 'y2' in pared.attrib:
                y = max(y, int(pared.attrib['y2']))
                self.__paredes[(x, y)] |= Direccion.ESTE
                self.__paredes[(x + 1, y)] |= Direccion.OESTE

    @property
    def version(self) -> str:
        """La versión del archivo de entrada."""
        return self.__version

    @property
    def x(self) -> int:
        """La posición x inicial de Karel."""
        return self.__x

    @property
    def y(self) -> int:
        """La posición y inicial de Karel."""
        return self.__y

    @property
    def w(self) -> int:
        """El ancho del mundo."""
        return self.__w

    @property
    def h(self) -> int:
        """"El alto del mundo."""
        return self.__h

    @property
    def direccion(self) -> str:
        """La orientación inicial de Karel.

        Puede ser uno de ['NORTE', 'ESTE', 'SUR', 'OESTE'].
        """
        return self.__direccion

    @property
    def instrucciones_maximas(self) -> int:
        """Instrucciones maximas a ejecutar"""
        return self.__instrucciones_maximas

    @property
    def longitud_stack(self) -> int:
        """El tamaño maximo que puede tener el stack"""
        return self.__longitud_stack

    @property
    def memoria_stack(self) -> int:
        """Memoria máxima del stack"""
        return self.__memoria_stack

    @property
    def llamada_maxima(self) -> int:
        """Número máximo de llamadas permitidas"""
        return self.__llamada_maxima

    def limite_comando(self, comando: str) -> Optional[int]:
        """Regresa el número máximo de veces que se puede usar un comando

        Si no hay límite, regresa None
        """
        return self.__limites.get(comando, None)

    @property
    def mochila(self) -> Cantidad:
        """El número de zumbadores en la mochila de Karel.

        Puede ser un entero o la cadena 'INFINITO'.
        """
        return self.__mochila

    @property
    def despliega(self) -> List[str]:
        """Lista de elementos que se van a guardar en la salida.

        Puede ser uno de ['MUNDO', 'ORIENTACION', 'POSICION'].
        """
        return list(self.__despliega)

    @property
    def despliega_posicion(self) -> bool:
        """Si se va a desplegar la posición final de Karel en la salida."""
        return self.__despliega_posicion

    @property
    def despliega_orientacion(self) -> bool:
        """Si se va a desplegar la orientación final de Karel en la salida."""
        return self.__despliega_orientacion

    @property
    def despliega_mundo(self) -> bool:
        """Si se van a desplegar los zumbadores elegidos en la salida."""
        return self.__despliega_mundo

    @property
    def despliega_instrucciones(self) -> bool:
        """Si se va a desplegar el número de instrucciones en la salida."""
        return self.__despliega_instrucciones

    @property
    def lista_zumbadores(self) -> Dict[Casilla, Cantidad]:
        """Un diccionario con los zumbadores.

        Cada llave (x, y) tiene como valor el número de zumbadores en esa
        casilla.
        """
        return self.__zumbadores

    def zumbadores(self, casilla_x: int, casilla_y: int) -> Cantidad:
        """Regresa el número de zumbadores para la casilla en (x, y).

        Si hay una cantidad infinita de zumbadores, regresa la cadena
        'INFINITO'.
        """
        if (casilla_x, casilla_y) not in self.__zumbadores:
            return 0
        return self.__zumbadores[(casilla_x, casilla_y)]

    @property
    def mapa_paredes(self) -> DefaultDict[Casilla, Direccion]:
        """Un diccionario con las paredes del mundo.

        Cada llave (x, y) tiene como valor una máscara de bits
        con las paredes adyacentes a esa casilla.

        Las direcciones de la máscara están descritas en Direccion.
        """
        return collections.defaultdict(lambda: Direccion(0), self.__paredes)

    def paredes(self, casilla_x: int, casilla_y: int) -> Direccion:
        """Regresa una máscara de bits con las direcciones en
        las que hay una pared en la casilla (x, y).

        Las direcciones de la máscara están descritas en Direccion.
        """
        return self.__paredes[(casilla_x, casilla_y)]

    @property
    def lista_dump(self) -> Set[Casilla]:
        """El conjunto de casillas marcadas para generar una salida."""
        return set(self.__dump)

    def dump(self, casilla_x: int, casilla_y: int) -> bool:
        """Regresa True si la casilla está marcada para generar una salida."""
        return (casilla_x, casilla_y) in self.__dump

    def __repr__(self) -> str:
        """Imprime una versión bonita del objeto."""
        return '<libkarel.KarelInput %s>' % ', '.join(
            '%s=%r' % x for x in {
                'x': self.x,
                'y': self.y,
                'mochila': self.mochila,
                'direccion': self.direccion,
                'despliega': self.despliega,
            }.items())


class KarelOutput:
    """Representa un archivo .out."""
    def __init__(self, contents: str):
        self.root = ET.fromstring(contents)
        self.__zumbadores: Dict[Casilla, Cantidad] = {}
        for linea in self.root.findall('mundos/mundo/linea'):
            pos_y = int(linea.attrib['fila'])
            pos_x = 0
            for token in (linea.text or '').strip().split():
                if token[0] == '(':
                    pos_x = int(token[1:-1])
                else:
                    self.__zumbadores[(pos_x, pos_y)] = _cantidad(token)
                    pos_x += 1

        programa = self.root.find('programas/programa')
        if programa is not None:
            self.__resultado = programa.attrib['resultadoEjecucion']
        else:
            self.__resultado = 'FIN PROGRAMA'

        karel = self.root.find('programas/programa/karel')
        self.__x: Optional[int] = None
        self.__y: Optional[int] = None
        self.__direccion: Optional[str] = None
        if karel is not None:
            if 'x' in karel.attrib:
                self.__x = int(karel.attrib['x'])
                self.__y = int(karel.attrib['y'])
            if 'direccion' in karel.attrib:
                self.__direccion = karel.attrib['direccion']

        self.__instrucciones: Dict[str, Optional[int]] = {
            'avanza': None,
            'gira_izquierda': None,
            'coge_zumbador': None,
            'deja_zumbador': None,
        }
        instrucciones = self.root.find('programas/programa/instrucciones')
        if instrucciones is not None:
            for k in self.__instrucciones:
                if k in instrucciones.attrib:
                    self.__instrucciones[k] = int(instrucciones.attrib[k])

    @property
    def x(self) -> Optional[int]:
        """La posición x final de Karel. None si no se hizo dump posición."""
        return self.__x

    @property
    def y(self) -> Optional[int]:
        """La posición y final de Karel. None si no se hizo dump posición."""
        return self.__y

    @property
    def direccion(self) -> Optional[str]:
        """La orientación final de Karel.

        Puede ser uno de ['NORTE', 'ESTE', 'SUR', 'OESTE'], o None si no se
        hizo dump orientación."""
        return self.__direccion

    @property
    def resultado(self) -> str:
        """Una cadena con el resultado de la ejecución.

        'FIN PROGRAMA' significa ejecución exitosa.
        """
        return self.__resultado

    @property
    def error(self) -> bool:
        """True si no fue una ejecución exitosa."""
        return self.resultado != 'FIN PROGRAMA'

    @property
    def lista_zumbadores(self) -> Dict[Casilla, Cantidad]:
        """Un diccionario con los zumbadores.

        Cada llave (x, y) tiene como valor el número de zumbadores en esa
        casilla al final de la ejecución.
        """
        return dict(self.__zumbadores)

    @property
    def instrucciones(self) -> Dict[str, Optional[int]]:
        """Un diccionario con el número de instrucciones que karel ejecutó"""
        return self.__instrucciones

    def zumbadores(self, casilla_x: int, casilla_y: int) -> Cantidad:
        """Regresa el número de zumbadores para la casilla en (x, y)

        Si hay una cantidad infinita de zumbadores, regresa la cadena
        'INFINITO'.
        """
        if (casilla_x, casilla_y) not in self.__zumbadores:
            return 0
        return self.__zumbadores[(casilla_x, casilla_y)]

    def __repr__(self) -> str:
        """Imprime una versión bonita del objeto"""
        return '<libkarel.KarelOutput %s>' % ', '.join(
            '%s=%r' % x for x in {
                'x': self.x,
                'y': self.y,
                'direccion': self.direccion,
                'resultado': self.resultado,
                'error': self.error,
            }.items())


def load() -> Tuple[KarelInput, KarelOutput, str]:
    """Regresa (input, output, nombre de caso) para la ejecución actual"""
    with open('data.in', 'r') as data_in:
        return (KarelInput(data_in.read()), KarelOutput(sys.stdin.read()),
                sys.argv[1])


def load_dict() -> Dict[str, Union[str, KarelInput, KarelOutput]]:
    """Regresa un diccionario con información sobre la ejecución actual"""
    with open('data.in', 'r') as data_in, open('data.out', 'r') as data_out:
        return {
            'case_name': sys.argv[1],
            'contestant_output': KarelOutput(sys.stdin.read()),
            'case_input': KarelInput(data_in.read()),
            'case_output': KarelOutput(data_out.read()),
        }


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
