import sympy
import numpy
from sympy import *
from sympy.abc import _clash1, _clash2, _clash

meter, second, kg, ampere, kelvin, mole, candela, angstrom = sympy.symbols(
    'meter,second,kg,ampere,kelvin,mole,candela,angstrom', real=True, positive=True
)
ns = {}
ns.update(_clash)
ns.update(
    {
        'meter': meter,
        'second': second,
        'kg': kg,
        'ampere': ampere,
        'kelvin': kelvin,
        'mole': mole,
        'candela': candela,
        'pi': sympy.pi,
        'e': sympy.E,
        'I': sympy.I,
        'ff': sympy.Symbol('ff'),
        'FF': sympy.Symbol('FF'),
    }
)

# Sympy substitution rule for removing units from an expression
baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}
derivedunits = {
    'joule': kg * meter ** 2 / second ** 2,
    'newton': kg * meter ** 2 / second ** 2,
    'coulomb': ampere * second,
    'volt': kg * meter ** 2 / second ** 3 / ampere,
    'electronvolt': 1.6021766208 * 1.0e-19 * kg * meter ** 2 / second ** 2,
    'erg': 1.0e-7 * kg * meter ** 2 / second ** 2,
    'gram': 1.0e-3 * kg,
    'angstrom': 1.0e-10 * meter,
    'ohm': kg * meter ** 2 / second ** 3 / ampere ** 2,
}
ns.update(derivedunits)
