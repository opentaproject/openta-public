from exercises.models import Exercise, Question, Answer
from exercises.parsing import question_json_get, question_xmltree_get, exercise_xmltree
from exercises.util import nested_print
import json

question_check_dispatch = {}


class QuestionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def register_question_type(question_type, grading_function):
    question_check_dispatch[question_type] = grading_function


def question_check(user, exercise_key, question_key, answer_data):
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
    question_json = question_json_get(dbexercise.path, question_key)
    xmltree = exercise_xmltree(dbexercise.path)
    question_xmltree = question_xmltree_get(xmltree, question_key)
    global_xmltree = (
        xmltree.xpath('/exercise/global[@type="{type}"]'.format(type=dbquestion.type)) or [None]
    )[0]
    if dbquestion.type in question_check_dispatch:
        result = {}
        try:
            result = question_check_dispatch[dbquestion.type](
                question_json, question_xmltree, answer_data, global_xmltree
            )
        except QuestionError as e:
            return {'error': "XML error: " + str(e)}
        correct = False
        if 'correct' in result:
            correct = result['correct']
        if user.has_perm('exercises.log_question'):
            dbanswer = Answer.objects.create(
                user=user,
                question=dbquestion,
                question_key=dbquestion.question_key,
                exercise_key=dbexercise.exercise_key,
                answer=answer_data,
                grader_response=json.dumps(result),
                correct=correct,
            )
        return result
    else:
        return {'error': 'No grading function for question type ' + dbquestion.type}
