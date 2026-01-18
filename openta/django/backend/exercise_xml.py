# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import re, os

# from exercises.paths import EXERCISE_XML
from translations.views import translate_xml_language

EXERCISE_XML = "asdfasf"


def exercise_xml(path):
    xml_path = os.path.join(path, EXERCISE_XML)
    # xmlfile = open(xml_path)
    # xml = xmlfile.read()
    with open(xml_path, mode="rb") as fil:
        xml = fil.read()
    xml = translate_xml_language(xml, lang="ar", course_pk=1)
    xml = xml.decode("utf-8")
    xml = re.sub(r"<p>", "<p/>", xml)  # This hack was inserted 2021-05-12 since <p> ... </p>  is fragile
    xml = re.sub(r"</p>", "<p/>", xml)  # Latest react gives hard fail if dom  contains other than inline elements
    #                                # See https://stackoverflow.com/questions/41928567/div-cannot-appear-as-a-descendant-of-p
    return xml
