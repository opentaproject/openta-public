# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import csv
from sympy import *
from xml.etree.ElementTree import fromstring, ParseError
import hashlib, time
from django.conf import settings
from lxml import etree
import json
import re
import random
from random import shuffle, choice, sample, randint
import collections
import os.path


def macrolist_to_dict(localmacrolist):
    localmacros = localmacrolist
    localmacrodict = collections.OrderedDict()
    linesplitter = re.compile(r"(?<=[^\\]);")  # SPLIT ON NON LITERAL semicolon
    if localmacros:
        for localmacro in localmacros:
            lines = linesplitter.split(localmacro.text)
            for line in lines:
                try:
                    line = line.strip()
                    if not re.match(r"^#", line) and not line == '' :
                        patval = line.split(":=")
                        lhs = patval[0].strip()
                        pats = patval[0].strip().lstrip('[').rstrip(']')
                        patslist = [ i.strip() for i in pats.split(',') if not i == '']
                        for pat in patslist :
                            if not pat.startswith('@') :
                                raise MacroError(' macro variables must begin with \@ character')
                            val = ((patval[1].strip()).split("#"))[0]
                        localmacrodict[lhs] = val
                except MacroError  as err :
                    raise MacroError('variable must begin with @ sign', line )
                except Exception as err :
                    if not line == "":
                        raise MacroError(
                            'macro definition line with no macro;  \
                                     check for "=" sign instead of ":-" :  \
                                     Here is the offending line ',
                            line,
                        )
    return localmacrodict


def randomshuffle(lis):
    random.shuffle(lis)
    return lis


def fileread(filename, directory):
    path = os.path.join(directory, filename)
    file = open(path, "r")
    return file.read()


def randomoneof(lis):
    random.shuffle(lis)
    return lis[0]


def randomsamplefrom(n, lis):
    random.shuffle(lis)
    return lis[:n]


def randomsample(nmin, nmax, nvals):
    r = sample(range(int(nmin), int(nmax) + 1), int(nvals))
    return r


def randominteger(nmin, nmax):
    r = random.randint(int(nmin), int(nmax))
    return r


def randomforwardsort(X, Z):
    YN = [x for _, x in sorted(zip(Z, X))]
    return YN


def randominversesort(X, Y):
    try:
        YY = list(range(0, len(X)))
        Z = [yy for _, yy in sorted(zip(Y, YY))]
        YN = []
        for zitem in Z:
            YN.append(X[zitem])
        return YN
    except Exception as e:
        raise MacroError("randominversesort error:   X =  " + str(X) + "and Y = " + str(Y) + "Error = " + str(e))


def randomsortedsample(nmin, nmax, nvals):
    r = sample(range(int(nmax)), int(nvals))
    r.sort()
    return r


class MacroError(Exception):
    pass


def reducedict(combodict):
    vars = {}
    atsign = "ATSIGN"
    try:
        for lhs, rhs in combodict.items():
            if not str(lhs) == "@combined_user_macros":
                orig = str(lhs) + ":= " + str(rhs)
                lhsp = re.sub("@", atsign, lhs)
                rhsp = re.sub("@", atsign, rhs)
                rhsp = rhsp.strip().strip(';').strip();
                if not( ( rhsp[0] == '`' and rhsp[-1] == '`') or 'basic' in rhsp[0:6] ) : # BACKWARD COMPATIBLE
                    for key, val in vars.items():
                        val = val.replace("\\", "bAcKsLaSh")
                        rhsp = re.sub(str(key), str(val), rhsp)
                    line = str(lhsp) + " = " + rhsp
                    exec(line)
                else :
                    qtype = 'basic'
                    from exercises.questiontypes.basic.basic import BasicQuestionOps as nop
                    contents = re.sub(r"^basic","",rhsp)
                    contents = contents.strip('`');
                    asc =  nop.asciiToSympy( nop, contents)
                    symex = sympify( asc , nop.scope  )
                    rhsp = f"\"{symex}\""
                    line = str(lhsp) + " = " + rhsp
                    exec( line )

                vars = {k: str(v) for k, v in locals().items() if k.startswith(atsign)}
    except:
        raise MacroError("check line :", orig)
    vars = {re.sub(atsign, "@", k): str(v) for k, v in locals().items() if k.startswith(atsign)}
    return vars


def evaluate_random_in_rhs_of_macro(macrodict, usermacrodict, seed=0):
    if macrodict:
        random.seed(seed)
    combodict = collections.OrderedDict({})

    for k, v in usermacrodict.items():
        combodict[k] = "'" + str(v) + "'"
    for k, v in macrodict.items():
        combodict[k] = v
    vars = reducedict(combodict)
    return vars


def apply_macros_to_string(xmlstr, macrodictlist):
    oldstring = ""
    imax = 0
    while xmlstr not in oldstring:
        for macrodict in macrodictlist:
            for key in macrodict:
                lhs = str(key)
                if not "[" in lhs:
                    pat = str(key) + "(\\W|$|\\\"|\\')"
                    rhs = str(macrodict[key])
                    rhs = re.sub(r"\\", "bAcKsLaSh", rhs)  # temporary hack to deal with backslash
                    rhs = re.sub(r"\$", "dOlLaR", rhs)
                    sub = str(rhs) + "\\1"
                    xmlstr = re.sub(pat, sub, xmlstr)
                # else:
                #    print("multiassign")
            oldstring = xmlstr
            imax = imax + 1
            if imax > 10:
                raise MacroError(
                    "Too many attempts to recursively define xml string: imax =  "
                    + str(imax)
                    + "hit with "
                    + pat
                    + " := "
                    + rhs
                )
    return xmlstr


def apply_macros_to_node(node, usermacros):
    XMLCACHE = "/tmp/XMLCACHE"
    DO_XML_CACHING = False
    newnode = node
    xml = etree.tostring(node, encoding=str)
    if not "@" in xml:
        return node
    if len(usermacros) == 0:
        return node
    #### BEGIN MACRO CACNING
    # TODO
    username = usermacros["@user"]
    macrohash = (hashlib.md5(str(usermacros).encode("utf-8")).hexdigest())[:10]
    nodehash = (hashlib.md5(xml.encode("utf-8")).hexdigest())[:10]
    path = os.path.join(XMLCACHE, username)
    filename = "M_" + macrohash + "_N_" + nodehash + ".xml"
    xml_path = os.path.join(path, filename)
    if settings.DO_CACHE and DO_XML_CACHING and os.path.exists(xml_path):
        xmlfile = open(xml_path)
        xmlstr = xmlfile.read()
        newnode = etree.fromstring(xmlstr)
        return newnode
    ########  END MACROCACCHING

    tag = newnode.tag
    localmacros = newnode.findall("./macros")
    localmacrodict = macrolist_to_dict(localmacros)
    if len(localmacros) > 0:
        for localmacro in localmacros:
            try:
                newnode.remove(localmacro)
            except TypeError:
                pass
    xmlstr = etree.tostring(newnode, encoding=str)
    if tag == "question":
        seed = usermacros["@questionseed"]
    else:
        seed = usermacros["@exerciseseed"]
    localmacrodict = evaluate_random_in_rhs_of_macro(localmacrodict, usermacros, seed)
    xmlstr = apply_macros_to_string(xmlstr, [usermacros, localmacrodict])
    if not "@" in xmlstr:
        newnode = etree.fromstring(xmlstr)
        choices = newnode.findall("./*[@order]")
        clist = {}
        for choice in choices:
            order = choice.attrib["order"]
            clist[order] = choice
            newnode.remove(choice)
        skeys = sorted(clist.keys())
        for skey in skeys:
            newnode.append(clist[skey])
        xmlstr = etree.tostring(newnode, encoding=str)
    xmlstr = re.sub("bAcKsLaSh", "\\\\", xmlstr)
    xmlstr = re.sub("dOlLaR", "$", xmlstr)
    newnode = etree.fromstring(xmlstr)
    newquestions = []
    for child in newnode:
        if child.tag == "question":
            question = child
            question_key = str(question.attrib["key"])
            try:
                qusermacros = usermacros["@combined_user_macros"][question_key]
            except:
                qusermacros = usermacros
            newquestion = apply_macros_to_node(question, qusermacros)
            if not newquestion == question:
                newnode.remove(question)
                newquestions.append(newquestion)
    for question in newquestions:
        newnode.append(question)
    #
    # WRITE THE CACHING FILE AND UNLINK OLD
    #
    if DO_XML_CACHING:
        xml = etree.tostring(newnode, encoding=str)
        os.makedirs(path, exist_ok=True)
        with open(xml_path, "w") as file:
            file.write(xml)
        current_time = time.time()
        for f in os.listdir(path):
            xml_path = os.path.join(path, f)
            creation_time = os.path.getctime(xml_path)
            if (current_time - creation_time) > 600:
                os.unlink(xml_path)
    #
    # #ND CACHING INSERT
    #

    return newnode


def apply_macros_to_exercise(root, usermacros):
    if len(usermacros) > 0:
        newnode = apply_macros_to_node(root, usermacros)
    else:
        return root
    xml = etree.tostring(newnode, encoding=str)
    if " @" in xml:
        parts = xml.split(" @")[1]
        parts = re.sub(r"(\w+).*", " @\\1", parts, flags=re.DOTALL)
        raise MacroError(
            "Unexpanded macro token '"
            + parts
            + "' remains.  Check for missing semicolon in macrodefinition: \
                Use '&#64;' instead of the @ sign if you want to really use an @ sign in the xml"
        )
    return newnode


def inject_text_into_node(root, est):
    textnode = root.find("text")
    if textnode is None:
        for elem in root.getiterator():
            if elem.tail:
                elem.tail = est + elem.tail
                break
    else:
        textnode.text = est + textnode.text
    return root
