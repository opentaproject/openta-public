# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import ast
import html
from pathlib import Path

SRC = Path(__file__).with_name('functions.py')
OUT = Path(__file__).with_name('matrix_defs_doc.html')

source = SRC.read_text(encoding='utf-8')
tree = ast.parse(source, filename=str(SRC))

class_info = {}
func_info = {}

def get_eval_signature(cnode: ast.ClassDef):
    for b in cnode.body:
        if isinstance(b, ast.FunctionDef) and b.name == 'eval':
            args = [a.arg for a in b.args.args]
            # drop 'cls'/'self'
            args = [a for a in args if a not in ('cls', 'self')]
            if b.args.vararg is not None:
                args.append('*' + b.args.vararg.arg)
            if b.args.kwarg is not None:
                args.append('**' + b.args.kwarg.arg)
            return args
    return []

def get_signature(fnode: ast.FunctionDef):
    args = [a.arg for a in fnode.args.args]
    if fnode.args.vararg is not None:
        args.append('*' + fnode.args.vararg.arg)
    if fnode.args.kwarg is not None:
        args.append('**' + fnode.args.kwarg.arg)
    return args

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        doc = ast.get_docstring(node) or ''
        class_info[node.name] = {
            'doc': doc,
            'args': get_eval_signature(node)
        }
    elif isinstance(node, ast.FunctionDef):
        doc = ast.get_docstring(node) or ''
        func_info[node.name] = {
            'doc': doc,
            'args': get_signature(node)
        }

# find matrix_defs dict
matrix_defs = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'matrix_defs' and isinstance(node.value, ast.Dict):
                keys = node.value.keys
                vals = node.value.values
                for k, v in zip(keys, vals):
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        key = k.value
                        val_repr = None
                        ref_name = None
                        if isinstance(v, ast.Name):
                            ref_name = v.id
                            val_repr = ref_name
                        else:
                            try:
                                val_repr = ast.unparse(v)
                            except Exception:
                                val_repr = type(v).__name__
                        matrix_defs[key] = {
                            'value_repr': val_repr,
                            'ref_name': ref_name,
                        }

def parse_from_doc(doc: str):
    args_line = None
    result_line = None
    for raw in (doc or '').splitlines():
        line = raw.strip()
        low = line.lower()
        if low.startswith('function arguments:') or low.startswith('arguments:'):
            args_line = line.split(':', 1)[1].strip()
        if low.startswith('result:') or low.startswith('returns:'):
            result_line = line.split(':', 1)[1].strip()
    return args_line, result_line

def guess_args_and_result(key, ref_name, sig_args):
    k = (key or '').lower()
    r = (ref_name or '').lower()
    # default guesses
    args_guess = ', '.join(sig_args) if sig_args else ''
    result_guess = 'expression/value'

    boolish = {
        'isequal','eq','isnotequal','neq','isdiagonal','isdiagonalizable','ishermitian','isunitary',
        'areeigenvaluesof','isdiagonalizationof','areorthogonal','areeigenvectors of','areeigenvectorsof'
    }
    if k in boolish:
        return (args_guess or 'x, y', '1 or 0 (boolean)')

    if k in {'trace'}:
        return (args_guess or 'x (Matrix)', 'number (trace)')
    if k in {'rank','rankof','len'}:
        return (args_guess or 'x (Matrix)', 'integer')
    if k in {'dim','shape','dimensions'}:
        return (args_guess or 'x (Matrix)', 'Matrix([rows, cols])')
    if k in {'transpose','localtranspose','conjugate','localconjugate','adjoint','localadjoint','inverse','localinverse'}:
        return (args_guess or 'x (Matrix)', 'Matrix')
    if k in {'times'}:
        return (args_guess or 'x, y (Matrices)', 'Matrix (elementwise)')
    if k in {'mul'}:
        return (args_guess or 'a, b, ... (Matrices)', 'Matrix product')
    if k in {'sort'}:
        return (args_guess or 'x (Matrix)', 'Matrix (sorted)')
    if k in {'norm','abs'}:
        return (args_guess or 'x', 'nonnegative magnitude')
    if k in {'grad'}:
        return (args_guess or 'fun(x,y,z)', '3-vector (Matrix)')
    if k in {'del2'}:
        return (args_guess or 'fun(x,y,z)', 'scalar (Laplacian)')
    if k in {'curl'}:
        return (args_guess or 'M (3-vector)', '3-vector (Matrix)')
    if k in {'div','localdiv'}:
        return (args_guess or 'M (3-vector)', 'scalar (divergence)')
    if k in {'rotationmatrix'}:
        return (args_guess or 'n, theta', '3x3 Matrix')
    if k in {'rotationarguments'}:
        return (args_guess or 'm (Matrix)', '(vector, angle)')
    if k in {'eigenvalues'}:
        return (args_guess or 'x (Matrix)', 'FiniteSet of eigenvalues')
    if k in {'diagonalof','diagonalpart'}:
        return (args_guess or 'x (Matrix)', 'Matrix (diagonal)')
    if k in {'mlog','mexp'}:
        return (args_guess or 'x (Matrix)', 'Matrix (elementwise)')
    if k in {'matrixelements'}:
        return (args_guess or 'm, i or m, [i,j]', 'element or row/column Matrix')
    if k in {'array'}:
        return (args_guess or '(…)','Array')
    if k in {'exp','asin'}:
        return (args_guess or 'x','expression')
    if k in {'xhat','yhat','zhat','true','false','true','false'}:
        return ('', 'constant')
    return (args_guess, result_guess)

rows = []
for key, meta in matrix_defs.items():
    ref = meta.get('ref_name')
    doc = ''
    sig_args = []
    if ref and ref in class_info:
        doc = class_info[ref]['doc']
        sig_args = class_info[ref]['args']
    elif ref and ref in func_info:
        doc = func_info[ref]['doc']
        sig_args = func_info[ref]['args']

    doc_args, doc_result = parse_from_doc(doc)
    if doc_args or doc_result:
        args = doc_args or ', '.join(sig_args) or ''
        result = doc_result or 'expression/value'
    else:
        args, result = guess_args_and_result(key, ref, sig_args)

    rows.append((key, args, result))

rows.sort(key=lambda r: r[0].lower())

def esc(x):
    return html.escape(str(x or ''))

html_out = [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="utf-8" />',
    '  <title>matrix_defs: Functions, Args, Results</title>',
    '  <style>body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:16px}table{border-collapse:collapse;width:100%;max-width:1200px}th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}th{background:#f7f7f7}</style>',
    '</head>',
    '<body>',
    '  <h1>Functions from matrix_defs (functions.py)</h1>',
    '  <table>',
    '    <thead><tr><th>Function</th><th>Arguments</th><th>Result</th></tr></thead>',
    '    <tbody>'
]

for name, args, result in rows:
    html_out.append(f'      <tr><td>{esc(name)}</td><td>{esc(args)}</td><td>{esc(result)}</td></tr>')

html_out += [
    '    </tbody>',
    '  </table>',
    f'  <p>Source: {esc(str(SRC))}</p>',
    '</body>',
    '</html>'
]

OUT.write_text('\n'.join(html_out), encoding='utf-8')
print(f"Wrote {OUT}")

