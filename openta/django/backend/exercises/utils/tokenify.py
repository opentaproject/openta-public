# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.util import get_hash_from_string, index_of_matching_right_paren
import re as resub
from sympy import *


def dematrixify(sexpr, varsubs):
    matrix_subs = {}
    matrix_subs["xhat"] = Matrix([1, 0, 0])
    matrix_subs["yhat"] = Matrix([0, 1, 0])
    matrix_subs["zhat"] = Matrix([0, 0, 1])
    newvarsubs = {}
    vsubs = []
    for key, val in varsubs.items():
        (newval, vsub) = tokenify(str(val))
        newvarsubs[key] = sympify(newval)
        for item in vsub:
            (n, m) = item["value"].shape
            matrix_subs[item["name"]] = item["value"]
    (xtest, vsubs) = tokenify(sexpr)
    for item in vsubs:
        (n, m) = item["value"].shape
        matrix_subs[item["name"]] = item["value"]
    return (xtest, newvarsubs, matrix_subs)


def tokenify(xtest, vsubs=[]):
    try:
        nit = 0
        vsubs = []
        while True:
            vsub = {}
            p = resub.compile(r"Matrix")
            allm = list(p.finditer(xtest))
            if len(allm) == 0:
                break
            m = allm[0]
            (ibeg, ileft) = m.span()
            iright = index_of_matching_right_paren(ileft, xtest)
            head = xtest[0:ibeg]
            body = xtest[ibeg:iright]
            tail = xtest[iright:]
            bodyhash = get_hash_from_string(body)
            vsub["name"] = bodyhash
            vsub["value"] = sympify(body)
            xtest = head + "(" + bodyhash + ")" + tail
            vsubs = vsubs + [vsub]
            nit = nit + 1
    except Exception as e:
        # print("FAILED WITH ", xtest)
        raise TypeError(f"Unidentified error E19234 {type(e).__name__}  Matrix dimensions inconsistent? ")
    return (xtest, vsubs)
