from collections import OrderedDict
import functools
import operator
from lxml import etree
import logging
import re
import json
import xmltodict


def parsehints(question_xmltree, global_xmltree, answer_data):
    xmllist = [question_xmltree, global_xmltree]
    hintstruc = []
    for xmlentry in xmllist:
        print("XML ENTRY = ", xmlentry)
        if xmlentry is not None:
            print("xmlentry = ", xmlentry)
            print("xmlentry.tag", xmlentry.tag)
            tag = xmlentry.tag
            qjson = (xmltodict.parse(etree.tostring(xmlentry))).get(tag).get('hint', False)
            print("qjson = ", qjson)
            if qjson:
                try:
                    for item in qjson:
                        print("ITEM = ", item)
                        p = item.get('regex')
                        r = item.get('warning')
                        hintstruc.append({p: r})
                    print("QSON ITEM regex", item.get('regex'))
                    print("QSON ITEM warning", item.get('warning'))
                except:
                    p = qjson.get('regex')
                    r = qjson.get('warning')
                    hintstruc.append({p: r})
            print(" FAILED qjson = ", qjson)
    print("hintstruc = ", hintstruc)
    result = {}
    for ahint in hintstruc:
        for p, r in ahint.items():
            print("p,r = ", p, r)
            if re.search(p, answer_data):
                print("CAUGHT THE STRING", p, " IN ", answer_data, "REPLY WITH ", r)
                result['status'] = 'hint'
                result['correct'] = False
                result['warning'] = r
                return result

    return None


# BELOW PARSED JSON DIRECTLY
# hints = question_json.get('hint',False)
# if hints :
#    print("ANSWER DATA = ", answer_data )
#    result = {}
#    print("HINTS = ", hints )
#    print("TYPE of hints = ", type( hints) )
#    try:
#        for item in  hints:
#             p =  ( item['regex'] )['$']
#             r =  ( item['warning'] )['$']
#             print("HINT regex", ( item['regex'] )['$'] )
#             print("HINT warning", ( item['warning'] )['$'] )
#             if( re.search(p, answer_data) ):
#                    print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
#                    result['status'] = 'hint';
#                    result['correct'] = False;
#                    result['warning'] = r
#                    return result
#    except :
#        p = hints['regex']['$']
#        r = hints['warning']['$']
#        print("SINGLE HINT", p, r )
#        print("answer_data", answer_data)
#        if( re.search(p, answer_data) ):
#                    print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
#                    result['status'] = 'hint';
#                    result['correct'] = False;
#                    result['warning'] = r
#                    return result
