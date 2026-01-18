#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
Generate an XSD from an HTML table describing tags, their children, and attributes.

Input HTML format (per merged_children.html style):
- Rows where column 1 (first <td>) is non-empty define a tag and column 2 lists
  its permitted children as a comma-separated list, or the word 'any' for any child.
- Immediately following rows with empty column 1 list attributes in column 2.
- A third column may exist but is ignored.

Usage:
  xsd_from_html.py path/to/merged_children.html > derived.xsd

Notes:
- All attributes are emitted as xs:string.
- Elements are emitted with mixed="true" so text content is permitted.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate XSD from merged_children.html-style table")
    p.add_argument("html_file", help="Input HTML file with the Tag/Children/Attribute rows")
    return p.parse_args()


def extract_rows(doc: str) -> list[tuple[str, str]]:
    # Tolerant regex: capture first two cells of each table row
    row_re = re.compile(
        r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td",
        re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for m in row_re.finditer(doc):
        c1 = html.unescape(m.group(1)).strip()
        c2 = html.unescape(m.group(2)).strip()
        rows.append((c1, c2))
    return rows


def build_model(rows: list[tuple[str, str]]):
    order: list[str] = []
    attrs: dict[str, list[str]] = {}
    children: dict[str, list[str]] = {}
    current: str | None = None

    for c1, c2 in rows:
        if c1:  # new tag
            current = c1
            if current not in order:
                order.append(current)
            # parse children list
            kids = []
            if c2:
                if c2.lower() == "any":
                    kids = ["any"]
                else:
                    kids = [k.strip() for k in c2.split(",") if k.strip()]
            children[current] = kids
            attrs.setdefault(current, [])
        else:
            # attribute row for the most recent tag
            if current is None:
                continue
            if c2:
                attrs.setdefault(current, []).append(c2)

    # Add referenced child-only tags to order
    referenced = set()
    for kids in children.values():
        for k in kids:
            if k and k != "any":
                referenced.add(k)
    for tag in sorted(referenced - set(order)):
        order.append(tag)
        attrs.setdefault(tag, [])
        children.setdefault(tag, [])

    return order, children, attrs


def emit_xsd(order: list[str], children: dict[str, list[str]], attrs: dict[str, list[str]]) -> str:
    out = []
    w = out.append
    w('<?xml version="1.0" encoding="UTF-8"?>')
    w('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">')

    for tag in order:
        kids = children.get(tag, [])
        tag_attrs = [a.strip() for a in attrs.get(tag, []) if a.strip()]

        w(f'  <xs:element name="{tag}">')

        if kids == ["any"]:
            w('    <xs:complexType mixed="true">')
            w('      <xs:sequence>')
            w('        <xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/>')
            w('      </xs:sequence>')
            for a in tag_attrs:
                w(f'      <xs:attribute name="{a}" type="xs:string"/>')
            w('    </xs:complexType>')

        elif kids:
            w('    <xs:complexType mixed="true">')
            w('      <xs:choice minOccurs="0" maxOccurs="unbounded">')
            seen = set()
            for k in kids:
                if not k or k in seen:
                    continue
                seen.add(k)
                w(f'        <xs:element ref="{k}"/>')
            w('      </xs:choice>')
            for a in tag_attrs:
                w(f'      <xs:attribute name="{a}" type="xs:string"/>')
            w('    </xs:complexType>')

        else:
            if tag_attrs:
                w('    <xs:complexType mixed="true">')
                for a in tag_attrs:
                    w(f'      <xs:attribute name="{a}" type="xs:string"/>')
                w('    </xs:complexType>')
            else:
                w('    <xs:complexType mixed="true"/>')

        w('  </xs:element>')

    w('</xs:schema>')
    return "\n".join(out)


def main() -> int:
    args = parse_args()
    try:
        doc = Path(args.html_file).read_text(encoding="utf-8")
    except Exception as e:
        print(f"error: failed to read {args.html_file}: {e}", file=sys.stderr)
        return 2

    rows = extract_rows(doc)
    if not rows:
        print("error: no rows found (expecting <tr><td>..</td><td>..</td> ..)", file=sys.stderr)
        return 3

    order, kids, attrs = build_model(rows)
    xsd = emit_xsd(order, kids, attrs)
    sys.stdout.write(xsd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

