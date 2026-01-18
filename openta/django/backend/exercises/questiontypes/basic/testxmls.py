# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
import glob
from exercises.questiontypes.basic import BasicQuestionOps 
from exercises.questiontypes.matrix import MatrixQuestionOps 
from exercises.questiontypes.basic.basic  import IS_CORRECT
from exercises.models import get_qtype_from_xml
from sympy import Matrix
from exercises.parsing import exercise_xml_to_json 
from lxml import etree
from exercises.applymacros import apply_macros_to_node
import os
from exercises.views.api import validate_exercise_xml_
import pytest




def thispath():
    cwd = os.getcwd()
    thisdir =  os.path.dirname( os.getenv('PYTEST_CURRENT_TEST').split('::')[0] )
    head = cwd.split('exercises')[0];
    tail = thisdir.split('exercises')[1];
    path = f"{head}/exercises/{tail}"
    return path


class Test1_Basic(TestCase,  MatrixQuestionOps):

    @pytest.mark.django_db
    def test1 (self ):
        exerciseassetpath = thispath()
        #fp = open('exerciseassetpath/xmls/oneill-1-1-2.xml',"rb")
        path = f"{exerciseassetpath}"
        haserrors = False
        for root, dirname , files in os.walk(path,followlinks=True):
            for file in files :
                if  not '.swp' in file and '.xml' in  file and not 'history' in root  and not ':Trash' in root   and  not 'unitary' in root   and not 'broken1' in root  and not 'messy' in root :
                    #print(f"ROOT = {root}")
                    try: 
                        print(f" DO  ROOT = {root} FILENAME = {file}")
                        path = f'{root}'
                        fp = open(f'{root}/{file}',"rb")
                        xml = fp.read()
                        res = self.vchecknew( xml , path )
                        d = root.split('/')[-1]
                        sres = str(res);
                        #print(f"DO RES {d}/{file}  = {sres}")
                        assert not 'error' in sres
                    except Exception as e :
                        haserrors = True;
                        print(f"DO ERRORS ROOT {str(e)} IN {d}/{file}  = {sres}")
                        self.assertTrue(False)
        self.assertFalse( haserrors )


    def vchecknew( self , xml , path):
        user = 1
        exercise_key = 'abcdefg'
        db = 'openta'
        exerciseassetpath =  path
        extradefs = {}
        print(f"VCHECKNEW_EXERCISEASSETPATH = {path}")
        extradefs =  {"path" : path }
        res = validate_exercise_xml_(xml, user, exercise_key, db, path, extradefs )
        print(f"RES = {res}")
 

    def vcheckold( self , xml , path=None ) :
        root = etree.fromstring(xml)
        name = (root.xpath('./exercisename')[0]).text
        print(f"DO NAME = {name}")
        usermacros = {}
        usermacros['@user'] = '1' 
        usermacros['@exerciseseed'] = '121' 
        usermacros['@questionseed'] = '12342'

        root = apply_macros_to_node( root ,usermacros);
        xml_new = etree.tostring( root,encoding='UTF-8' ).decode();
        #print(f"xml_new = {xml_new}")
        question_xpath = f'/exercise/question'
        question_xmltrees = root.xpath(question_xpath)
        global_xpath = f'/exercise/global'
        global_xmltrees = root.xpath(global_xpath)
        global_xml = "";
        for global_xmltree in global_xmltrees:
            global_xml += etree.tostring( global_xmltree,encoding='UTF-8' ).decode();
        #print(f"glbal_xml = {global_xml}")
        #print(f"QUESTION_XMLTREE = {question_xmltrees} {len( question_xmltrees) } ")
        #ss = global_xml.replace('</global>','')
        ss = ''
        res = ''
        for question_xmltree in question_xmltrees :

            question_xmltree.attrib['user'] = '1' 
            question_xmltree.attrib['username'] = 'super'
            question_xmltree.attrib['exerciseassetpath'] = thispath() 
            question_xmltree.attrib['exercise_key'] =  'abcdefg'
            question_xmltree.attrib['subdomain'] =  'openta'


            atts = question_xmltree.attrib
            key = atts['key']
            #print(f"KEY = {key}")
            try :
                expression = ( question_xmltree.xpath('./expression')[0] ).text.strip()
                ss += f"answer{key} = {expression};\n"
            except  Exception as e  :
                pass

        #global_xml = ss + "</global>"
        #print(f"SS = {ss}")
        global_xml = global_xml.replace(f"</global>", ';' + ss + "</global>")
        if global_xml == '' :
            global_xml = "<global/>"
        global_xmltree = etree.fromstring( global_xml)
        #print(f"GLOBAL_XML = {global_xml}")
        res = {}
        for question_xmltree in question_xmltrees :
            question_xml = etree.tostring(question_xmltree, encoding='UTF-8' ).decode();
            qtype = question_xmltree.attrib.get('type',None)
            if qtype == None :
                qtype = get_qtype_from_xml( global_xml, question_xml, exercise_key="ABCDEFG", src="VCHECK")
            print(f"VCHECK QTYPE = {qtype}")
            if not qtype in [ 'multipleChoice' ,'text' ] :
            #print(f"QUESTION_XML = {question_xml}")
                atts = question_xmltree.attrib
                print(f"ATTS = {atts}")
                #print(f"ATTS = {atts}")
                question_json = exercise_xml_to_json( question_xml)
                question_json['@attr'] = question_xmltree.attrib
                #question_json['@attr']['key'] = "randomkey1";
                #question_json['@attr']['type'] ="default"
                key = atts['key']
                success = "error";
                msg = "FAILED"
                try :
                    (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
                except Exception as err :
                    msg = str(err)
                print(f"DO SUCCESS = {success} {msg} {name}" )
                res[key] = (success,msg)
        print(f"DONE {name}")
        return res
        #self.assertTrue( success == 'success' )
