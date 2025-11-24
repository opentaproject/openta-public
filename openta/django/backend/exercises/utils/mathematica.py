# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import re as reg

from sympy import srepr

from .string_formatting import ascii_to_sympy


def mathematica_form(student_answer):
    # print("STUDENT_ANSWER = ", student_answer)
    s = str(srepr(sympy.sympify(ascii_to_sympy(student_answer))))
    # print("S = ", s )
    s = reg.sub(r"\'", "", s)
    s = reg.sub(r"\[", "{", s)
    s = reg.sub(r"\]", "}", s)
    s = reg.sub(r"\(", "[", s)
    s = reg.sub(r"\)", "]", s)
    s = reg.sub(r"Global.", "", s)
    translations = {
        "Mul": "Times",
        "Pow": "Power",
        "Add": "Plus",
        "Integer": "Identity",
        "Symbol": "Identity",
        "cos": "Cos",
        "sin": "Sin",
        "tan": "Tan",
        "pi": "Pi",
        "abs": "Abs",
    }
    for key in translations.keys():
        s = reg.sub(r"%s" % key, translations[key], s)
    s = reg.sub(r"Identity\[([^\]]+)\]", r"\1", s)
    s = reg.sub(r"MutableDenseMatrix", "Identity", s)
    # print("S = ", s )
    return s
