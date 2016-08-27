from exercises.models import Exercise, Question
from exercises.parsing import question_json_get
from exercises.util import nested_print


def question_check_compare_numeric(question_json, answer_data):
    print('Check numeric!')
    return {'correct': False}


question_check_dispatch = {'compareNumeric': question_check_compare_numeric}


def question_check(exercise_key, question_key, answer_data):
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
    question_json = question_json_get(dbexercise.path, question_key)
    nested_print(question_json)
    if dbquestion.type in question_check_dispatch:
        result = question_check_dispatch[dbquestion.type](question_json, answer_data)
        return result
    else:
        return {'error': 'No grading function for question type ' + dbquestion.type}

    # print(JSON.dumps(json, indent=4))
    # print(JSON.dumps(deep_get(json,'problem','thecorrectanswer'), indent=4))
    '''
    proper_questions = legacy_process_questions(questions)
    question = None
    matched = list(filter(lambda x: x.get('@id') == question_id, proper_questions))
    ingress_match = list(filter(lambda x: x.get('@id') == 'ingress', questions))

    if len(matched) == 1:
        question = matched[0]
    else: 
        raise Exception('Invalid question id')

    if len(ingress_match) == 1:
        ingress = ingress_match[0]
    else: 
        raise Exception('No question ingress')
    if question:
        #variables = parseIngress(questions[0].get('$'))
        variables = parseIngress(ingress.get('$'))
        correct = question.get('$').replace(';','')
        result = symbolic.compareNumeric(JSON.dumps(variables), expression, correct)
        latex = {
                'latex': symbolic.toLatex(expression)
                }
        result.update(latex)
        #Need to merge with result dictionary...
        return result
'''
