from collections import OrderedDict
import functools
import operator
from lxml import etree
import logging
import re
import json
from django.utils import translation
from exercises.parsing import get_translations


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
    # print("PARSEHINTS ANSWERDATA = ", answer_data)
    # print("in parsehints question xmltree",  etree.tostring(question_xmltree , pretty_print=True) )
    # print("in parsehints global xmltree",  etree.tostring(global_xmltree, pretty_print=True) )
    lang = translation.get_language()
    # print( "CURRENT LANGUAGE = ", lang)
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
                        regex = item.find('regex').text
                        reply = item.find('comment').text
                        # alts = item.find('comment').findall('alt')
                        # alts2  = get_translations( item.find('comment'))
                        # print('alt2 = ', alts2)
                        # print('translation', alts2.get(lang, reply) )
                        tdict = get_translations(item.find('comment'))
                        reply = tdict.get(lang, reply)
                        # print("newreply = ", newreply)
                        # if alts:
                        #    print("alts = ", alts)
                        #    for alt in alts:
                        #        print("alt.get lang", alt.get('lang') )
                        #        if alt.get('lang') == lang :
                        #            reply = alt.text
                        presence = 'forbidden'
                        # print("p attrib = ", item.find('regex').attrib  )
                        attributedict = item.find('regex').attrib
                        if attributedict:
                            presence = attributedict.get('present', 'forbidden')
                            # print('presence = ', presence )
                        if regex and reply:
                            found = re.search(regex, answer_data)
                            if presence == 'forbidden' and found:
                                result['correct'] = False
                                result['comment'] = reply
                                result['dict'] = tdict
                                return result
                            elif presence == 'allowed' and found:
                                result['comment'] = reply
                                result['dict'] = tdict
                                return result
                            elif presence == 'necessary' and not found:
                                result['correct'] = False
                                result['comment'] = reply
                                result['dict'] = tdict
                                return result
                    # print("QSON ITEM regex",  item.get('regex') )
                    # print("QSON ITEM comment",  item.get('comment') )
                except:
                    # print("SHOULD NOT GET HERE ANY MORE; qjson is not a list; see parsehints")
                    result['correct'] = False
                    result['comment'] = 'PROGRAMMING ERROR; please inform admin HINT TAGS ARE WRONG'
                    return result
    #
    return None
