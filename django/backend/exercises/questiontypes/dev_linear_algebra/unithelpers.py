import sympy
import numpy
from sympy import sympify, symbols
from sympy.abc import _clash1, _clash2, _clash

units = 'meter,second,kg,ampere,kelvin,mole,candela'

meter, second, kg, ampere, kelvin, mole, candela = sympy.symbols(units, real=True, positive=True)
units = units.split(',')
sympy_units = [meter, second, kg, ampere, kelvin, mole, candela]

ns = {}
syms = ['C', 'O', 'Q', 'N', 'I', 'E', 'S', 'beta', 'zeta', 'gamma', 'pi']
syms = ['N', 'I', 'E', 'pi']
syms = ['N']
myclash = dict([( x , _clash[x] ) for x in syms ])

#ns.update(myclash)
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
        'N' : sympy.Symbol('N')
    }
)

# Sympy substitution rule for removing units from an expression
baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}

derivedunits = {
    'joule': kg * meter ** 2 / second ** 2,
    'Newton': kg * meter / second ** 2,
    'coulomb': sympy.sympify(ampere * second),
    'volt': sympy.sympify(kg * meter ** 2 / second ** 3 / ampere),
}
ns.update(derivedunits)
