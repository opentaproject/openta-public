# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import copy
import hashlib
import logging
import re
from xml.etree.ElementTree import Element
from lxml import etree, html
from xml.dom import minidom

logger = logging.getLogger(__name__)


def hshkey(txt: str) -> str:
    logger.debug(f"{txt=}")
    txt = " ".join(txt.split())
    return (hashlib.md5(txt.encode()).hexdigest())[0:7]


def string_to_xml(xml: str) -> Element:
    logger.debug(f"{xml=}")
    parser = etree.XMLParser(recover=True)
    return etree.fromstring(xml, parser=parser)


def xml_stripped_of_tags(elem: Element, tag: str) -> str:
    logger.debug(f"{elem.text=}, {tag=}")
    elemstripped = copy.deepcopy(elem)
    etree.strip_attributes(elemstripped)
    otheralts = elemstripped.findall(tag)
    for otheralt in otheralts:
        elemstripped.remove(otheralt)
    xml = etree.tostring(elemstripped, encoding=str)
    logger.debug(f"{xml=}")
    return xml


def elem_to_ascii(elem: Element) -> str:
    logger.debug(f"{elem=}")
    return html_content(xml_stripped_of_tags(elem, "alt"))


def elem_to_hashkey(elem: Element) -> str:
    logger.debug(f"{elem=}")
    return hshkey(elem_to_ascii(elem))


def html_content(txt: str) -> str:
    logger.debug("txt as xml: %s",  html.tostring(etree.fromstring(txt), encoding=str))
    txt = re.sub(r"^\s*<[^>]+>", "", txt)
    txt = re.sub(r"</[^>]+>\s*$", "", txt)
    txt = txt.strip()
    logger.debug(f"html content: {txt=}")
    return txt


def makepretty(xml: str) -> str:
    logger.debug(f"{xml=}")
    xmlout = xml
    xmlout = re.sub(r"\s+", " ", xmlout)
    xmlout = minidom.parseString(xmlout).toprettyxml()
    xmlout = re.sub(r"\s*\n\s*\n", "\n", xmlout)
    xmlout = re.sub(r"&quot;", '"', xmlout)
    return xmlout
