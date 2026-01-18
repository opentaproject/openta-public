# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import sympy

# from sympy.abc import _clash1, _clash2, _clash

units = "meter,second,kg,ampere,kelvin,mole,candela"

meter, second, kg, ampere, kelvin, mole, candela = sympy.symbols(units, real=True, positive=True)
units = units.split(",")
sympy_units = ["meter", "second", "kg", "ampere", "kelvin", "mole", "candela"]

ns = {}
syms = ["C", "O", "Q", "N", "I", "E", "S", "beta", "zeta", "gamma", "pi"]
syms = ["N", "I", "E", "pi"]
syms = ["N"]
# myclash = dict([(x, _clash[x]) for x in syms])

# ns.update(myclash)
ns.update(
    {
        "meter": meter,
        "second": second,
        "kg": kg,
        "ampere": ampere,
        "kelvin": kelvin,
        "mole": mole,
        "candela": candela,
        "pi": sympy.pi,
        "e": sympy.E,
        "I": sympy.I,
        "N": sympy.Symbol("newton"),
        #'ff': sympy.Symbol('ff'),
        #'FF': sympy.Symbol('FF'),
        #'N': sympy.Symbol('N'),
    }
)

# Sympy substitution rule for removing units from an expression
baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}
unitbaseunits = {
    "meter": 1.0,
    "second": 1.0,
    "kg": 1.0,
    "ampere": 1.0,
    "kelvin": 1.0,
    "mole": 1.0,
    "candela": 1.0,
}
derivedunits = {
    "joule": (kg * meter ** 2) / second ** 2,
    "newton": (kg * meter) / second ** 2,
    "coulomb": ampere * second,
    "volt": (kg * meter ** 2) / (ampere * second ** 3),
    "ohm": (kg * meter ** 2) / (ampere ** 2 * second ** 3),
    "watt": (kg * meter ** 2) / second ** 3,
    "farad": (ampere ** 2 * second ** 4) / (kg * meter ** 2),
    "chie": 1,
    "siemens": (ampere ** 2 * second ** 3) / (kg * meter ** 2),
    "tesla": kg / (ampere * second ** 2),
    "weber": (kg * meter ** 2) / (ampere * second ** 2),
    "henry": (kg * meter ** 2) / (ampere ** 2 * second ** 2),
    "mu_zero": (kg * meter * sympy.pi) / (2500000 * ampere ** 2 * second ** 2),
    "speed_of_light": (2.99792458 * 10 ** (8) * meter) / second,
    "mu_units": (kg * meter) / (ampere ** 2 * second ** 2),
    "mu_zero": sympy.pi / 2500000 * (kg * meter) / (ampere ** 2 * second ** 2),
    "mu_units": (kg * meter) / (ampere ** 2 * second ** 2),
    "epsilon_units": (ampere ** 2 * second ** 4) / (kg * meter ** 3),
    "epsilon_zero": 8.85418781762039 * 10 ** (-12) * (ampere ** 2 * second ** 4) / (kg * meter ** 3),
}
ns.update(derivedunits)
