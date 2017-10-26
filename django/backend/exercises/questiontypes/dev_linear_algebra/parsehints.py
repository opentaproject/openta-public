from collections import OrderedDict
import functools
import operator
from lxml import etree
import logging
import re
import json

# def parse_xml_variables(node):
#    '''
#    Parses variables defined through the XML syntax <var>...</var>
#    '''
#    variables = node.xpath('./var')
#    res = []
#    if variables is None:
#        return res
#    for var in variables:
#        token = var.find('token')
#        value = var.find('val')
#        if token is not None and value is not None:
#            res.append({'name': token.text, 'value': value.text})
#    return res


def parsehints(question_xmltree, global_xmltree, answer_data):
    # print("in parsehints question xmltree",  etree.tostring(question_xmltree , pretty_print=True) )
    # print("in parsehints global xmltree",  etree.tostring(global_xmltree, pretty_print=True) )
    xmllist = [question_xmltree, global_xmltree]
    # hintstruc = [];
    result = {}
    for xmlentry in xmllist:
        # print("XML ENTRY = ", xmlentry )
        # print("in xmlentry ",  etree.tostring(xmlentry, pretty_print=True) )
        if xmlentry is not None:
            # print("xmlentry = ", xmlentry)
            # print("xmlentry.tag", xmlentry.tag)
            hints = xmlentry.findall('hint')
            # print('hints= ', hints)
            if hints:
                if not isinstance(hints, list):
                    hints = [hints]
                try:
                    for item in hints:
                        # print("iTEM = ", item )
                        p = item.find('regex').text
                        r = item.find('warning').text
                        # print("p,r = ", p,r)
                        if p and r:
                            if re.search(p, answer_data):
                                # print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
                                result['status'] = 'hint'
                                result['correct'] = False
                                result['warning'] = r
                                # print("result = ", result)
                                return result
                    # print("QSON ITEM regex",  item.get('regex') )
                    # print("QSON ITEM warning",  item.get('warning') )
                except:
                    print("SHOULD NOT GET HERE ANY MORE; qjson is not a list; see parsehints")
                    result['correct'] = False
                    result['warning'] = "SOMETHING WRONG IN HINT PARSING"
                    return result
                    # p = qjson.get('regex',False)
                    # r = qjson.get('warning',False)
                    # if( p and r ):
                    #    if( re.search(p, answer_data) ):
                    #        #print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
                    #        result['status'] = 'hint';
                    #        result['correct'] = False;
                    #        result['warning'] = r
                    #        return result
                    # hintstruc.append({p:r})
    #     print(" FAILED qjson = ", qjson)
    # print("hintstruc = ", hintstruc)
    # for ahint in hintstruc:
    #    for p,r in ahint.items():
    #        print("p,r = ",p,r)
    #        if( re.search(p, answer_data) ):
    #            print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
    #            result['status'] = 'hint';
    #            result['correct'] = False;
    #            result['warning'] = r
    #            return result
    #
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


# def parsehints(question_xmltree, global_xmltree, answer_data):
#    xmllist  = [ question_xmltree, global_xmltree ]
#    hintstruc = [];
#    for xmlentry in xmllist:
#      print("XML ENTRY = ", xmlentry )
#      if xmlentry is not None:
#         print("xmlentry = ", xmlentry)
#         print("xmlentry.tag", xmlentry.tag)
#         tag = xmlentry.tag
#         qjson = ( xmltodict.parse( etree.tostring( xmlentry ) ) ).get(tag).get('hint',False)
#         print("qjson = ", qjson)
#         if qjson:
#            try:
#                for item in qjson:
#                    print("ITEM = ", item )
#                    p = item.get('regex')
#                    r = item.get('warning')
#                    hintstruc.append(  {p:r}  )
#                print("QSON ITEM regex",  item.get('regex') )
#                print("QSON ITEM warning",  item.get('warning') )
#            except:
#                p = qjson.get('regex')
#                r = qjson.get('warning')
#                hintstruc.append({p:r})
#         print(" FAILED qjson = ", qjson)
#    print("hintstruc = ", hintstruc)
#    result = {}
#    for ahint in hintstruc:
#        for p,r in ahint.items():
#            print("p,r = ",p,r)
#            if( re.search(p, answer_data) ):
#                print("CAUGHT THE STRING" , p , " IN ", answer_data , "REPLY WITH ", r )
#                result['status'] = 'hint';
#                result['correct'] = False;
#                result['warning'] = r
#                return result
#
#    return None
#
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
