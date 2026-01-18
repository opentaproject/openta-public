# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from django.conf import settings
from django.contrib.auth.models import User, Group
import re

from exercises.question import (  # This function is used to register the question type
    get_number_of_attempts,
    get_safe_previous_answers,
)
from exercises.utils.variableparser import (
    get_more_functions_from_obj,
    get_more_variables_from_obj,
    get_used_variable_list,
    remove_blacklist_variables_from_obj,
)


logger = logging.getLogger(__name__)


def json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback):
    expressions =  full_question.get("expression")
    if expressions :
        if not isinstance( expressions, list ) :
            expressions = [expressions];
        for expression in expressions :
            correct_answer = expression.get("$", "NO TEXT IN EXPRESSION").split(";")[0]
            used_variable_list = get_used_variable_list(correct_answer)
    else :
        used_variable_list = []
    variablelist = get_more_variables_from_obj(full_question.get("variables", {}), used_variable_list)
    variablelist = get_more_functions_from_obj(full_question.get("global", {}), variablelist)
    attr = full_question.get("@attr",None);
    if (full_question.get("@attr").get("exposeglobals", "false")).lower() == "true":
        safe_question["exposeglobals"] = True
        variablelist = get_more_variables_from_obj(full_question.get("global", {}), variablelist)

    else:
        safe_question["exposeglobals"] = False
    blacklists = [];
    blacklists.append( full_question.get("global",{}).get("blacklist",{}) )
    blacklists.append( full_question.get("global",{}).get("variables",{}).get("blacklist",{}) )
    blacklists.append( full_question.get("variables",{}).get("blacklist",{}) )
    blacklists.append( full_question.get("blacklist",{} ) )
    feedback = full_question.get("@attr").get("feedback", feedback)
    safe_question["feedback"] = feedback
    if feedback is False:
        safe_question["correct"] = None
    if safe_question["exposeglobals"]  :
        used_variable_list = get_more_variables_from_obj(full_question.get("global", {}), used_variable_list)
    for blacklist in blacklists :
        if not blacklist == None :
            variablelist = remove_blacklist_variables_from_obj(blacklist, variablelist)
            used_variable_list = remove_blacklist_variables_from_obj(blacklist, used_variable_list)
    used_variable_list = get_more_variables_from_obj( full_question.get("variables",{}), used_variable_list )
    lvars_ = full_question.get('vars',{}).get("$",'').split(',')
    lvars = [ i.strip() for i in lvars_ ]
    lvars = [ i for i in lvars if not i == '' ]
    if lvars :
        used_variable_list = list( set( used_variable_list + lvars ) )
    safe_question["username"] = user_id
    safe_question["used_variable_list"] = used_variable_list # [re.sub(r"variable", "", item) for item in variablelist]
    safe_question["is_staff"] = full_question.get('is_staff', False )
    safe_question['DUMMY_JSON_ENTRY'] = 'DUMMY_JSON_ENTRY'
    safe_question['db'] = full_question.get('db')
    db =  full_question.get('db')
    if not settings.RUNTESTS :
        safe_question["n_attempts"] = get_number_of_attempts(question_id, user_id)
        safe_question["previous_answers"] = get_safe_previous_answers(question_id, user_id, n_answers=settings.N_ANSWERS, feedback=feedback,db=db)
    v = safe_question["used_variable_list"] ;
    return safe_question

