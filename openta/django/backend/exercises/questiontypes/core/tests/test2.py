# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
from exercises.questiontypes.core import CoreQuestionOps 
from exercises.questiontypes.core.core  import IS_CORRECT
from exercises.parsing import exercise_xml_to_json 
from lxml import etree
import os

def thispath():
    cwd = os.getcwd()
    thisdir =  os.path.dirname( os.getenv('PYTEST_CURRENT_TEST').split('::')[0] )
    head = cwd.split('exercises')[0];
    tail = thisdir.split('exercises')[1];
    path = f"{head}/exercises/{tail}"
    return path


class Test1_Core(TestCase, CoreQuestionOps):

    def test0_simple (self ):
        exerciseassetpath = thispath()
        global_xml = "  <global/> "
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f" <question key=\"0\" type=\"core\">\
               <expression>2</expression> \
               <expression>3</expression> \
               </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, "2", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "3", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "4", global_xmltree  )
        self.assertFalse( r.get('correct',False) );

    def test_validate_isfalse_1( self ):
        exerciseassetpath = thispath()
        global_xml = "  <global>a = 1 ;  b = 2;     </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"true\" type=\"default\">\
            <istrue> $$ == -1 </istrue> \
            <isfalse> $$ == 0    <if-not-so>Should not be zero</if-not-so> </isfalse>  \
            <expression> a - b </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        print(f"CVALIDATE_QUESTION")
        r  = self.validate_question(question_json, question_xmltree, global_xmltree)
        print(f"TEST R = {r}")
        (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
        self.assertTrue( success == 'success' )
        r =  self.answer_check(  question_json, question_xmltree, " a-b ", global_xmltree  )
        print(f"RETURN FALSE {r}")
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "0 ", global_xmltree  )
        print(f"RA0 = {r}")
        self.assertFalse( r.get('correct',True) );
        self.assertTrue( 'Should not be zero' in r.get('error') )
        r =  self.answer_check(  question_json, question_xmltree, "1 ", global_xmltree  )
        print(f"RA1 = {r}")
        self.assertFalse( r.get('correct',True) );

    def test_validate_isfalse_2( self ):
        exerciseassetpath = thispath()
        global_xml = "  <global>a = 2  ; b = 1 ;     </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"true\" type=\"default\">\
            <expression> a - b   </expression> \
            <isfalse> $$ == 0    <if-not-so>Should not be zero</if-not-so> </isfalse>  \
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        question_json['@attr']['type'] ="core"
        rr =  self.validate_question(question_json, question_xmltree, global_xmltree)
        print(f"RR = {rr}")
        (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
        self.assertTrue( success == 'success' )
        r =  self.answer_check(  question_json, question_xmltree, " a-b ", global_xmltree  )
        self.assertTrue( r['correct'] )
        r =  self.answer_check(  question_json, question_xmltree, "0 ", global_xmltree  )
        print(f"R = {r}")
        self.assertFalse( r['correct'] )
        self.assertTrue( 'Should not be zero' == r['error'] )
        r =  self.answer_check(  question_json, question_xmltree, "1 ", global_xmltree  )
        self.assertTrue( r['correct'] );







    def test_simple( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( IS_CORRECT in r.get('comment'));

        r =  self.answer_check(  question_json, question_xmltree, "  Fa * v1   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'v1' in r.get('warning',"") );

        r =  self.answer_check(  question_json, question_xmltree, "  Fa * vf( 43)    ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'vf' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, "  Fa * Fb * vf( 43)    ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'vf' in r.get('warning',"") );



    def test_isfalse( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4.234  kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS FALSE SO IT ACCEPTS EVERYTHING
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue > $$ ==   sqrt( Fa^2 + Fb^2) \
                    <if-so> PASS1 </if-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2); </expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        print(f"1")

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        print(f"RR1 = {r}")
        self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'PASS1' in r.get('comment',"") );
        print(f"2")
        #self.assertTrue( 'Units OK' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );
        print(f"3")
        #self.assertTrue( 'Units OK' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        print(f"4")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );
        #elf.assertTrue( 'Units OK' in r.get('warning',"") );



    def test_isfalse0( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4.98234  kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue > $$ ==   sqrt( Fa^2 + Fb^2 )  \
                    <if-so> PASS1 </if-so>\
                    <if-not-so> FAIL1 </if-not-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        print(f"RC1 {r}")
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( 'PASS1' in r.get('comment'));
        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        print(f"RC2 {r}")
        self.assertFalse( r.get('correct',False) ); # SINCE SUFFICIENT = False it goes on to test expression
        self.assertTrue( 'FAIL1' in r.get('error','') ); # SINCE SUFFICIENT = False it goes on to test expression
        #self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        print(f"RC3{r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        print(f"RC4 {r}")
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " newvar * Fa + Fb   ", global_xmltree  )
        print(f"RC5 {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'Undefined' in r.get('warning',"") and 'newvar' in r.get('warning',"") );



    def test_isfalse1( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3.9 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);

        ##
        ## NOTE SUFFICIENCY CONDITION IS FALSE SO IT GOES ON TO TEST FURTHER
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue> $$ ==   sqrt( Fa^2 + Fb^2 )\
                    <if-so> PASS1 </if-so>\
                    <if-not-so> FAIL1 </if-not-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        #print(f"R = {r}")
        self.assertTrue( r.get('correct',False) );

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );



        #r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        #print(f"R = {r}")
        #self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );
        #self.assertTrue( 'NOMAG' in r.get('error',"") );



    def test_isfalse2( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue sufficient=\"True\" > $$ ==  sqrt( Fa^2 + Fb^2) \
                    <if-not-so> NOMAG </if-not-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        #print(f"R = {r}")
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOMAG' in r.get('error',"") );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );







    def test_blacklist(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            <blacklist><token> i </token></blacklist>\
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" type=\"default\">\
            <blacklist><token>j</token></blacklist>\
            <expression> a * b   </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['type'] ="core"
        full_question['used_variable_list'] = ['a','b'];
        full_question['is_staff'] = True;
        full_question["exposeglobals"] = False;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        safe_question['is_staff'] = True ;
        print(f"SAFE_QUESTION = {safe_question}")
        self.used_variable_list = ['a','b'] ; # THIS SUPPOSES BLACKLIST HAS BEEN PARSED PROPERLY by json_hook
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        print(f"RR0 = {r}")
        self.assertTrue( r['correct']  );
        safe_question['is_staff'] = False ;
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        print(f"RR1 = {r}")
        self.assertTrue( 'Not valid variables' in r['warning'] );
        r =  self.answer_check(  safe_question, question_xmltree, "a b + j ", global_xmltree  )
        print(f"RR2 = {r}")
        self.assertTrue( 'Not valid variables' in r['warning'] );


    def test_exposeglobals(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"True\" type=\"core\">\
            <expression> a * b  ;  </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['exposeglobals'] = 'True'
        full_question['@attr']['type'] ="core"
        full_question['used_variable_list'] = ['a','b','i','j'];
        full_question['is_staff'] = False ;
        full_question["exposeglobals"] = "True" ;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, 'randomkey1', '1' ,'exercise_key', feedback=True) 
        safe_question['used_variable_list'] = ['a','b','i','j']; # THIS SHOULD BE OBTAINED BY JSON_HOOK BUT IT IS TOO CONVOLUTED
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        self.assertTrue( r['correct'] )
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b  ", global_xmltree  )
        self.assertTrue(r['correct'] );

        




    def dead_code_test_exposeglobals(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"True\" type=\"core\">\
            <expression> a * b  ;  </expression>\
            </question>"
        xml = f"<exercise><exercisename> TEST </exercisename>\n\
                {global_xml}\n\
                {question_xml}\n\
                </exercise>"
        exercise_json = exercise_xml_to_json( xml)
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['exposeglobals'] = 'True'
        full_question['@attr']['type'] ="core"
        full_question['used_variable_list'] = ['a','b','i','j'];
        full_question['is_staff'] = False ;
        full_question["exposeglobals"] = "True" ;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, 'randomkey1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b  ", global_xmltree  )
        print(f"R = {r}")
        self.assertTrue( 'not valid' in r.get('warning') );

        




