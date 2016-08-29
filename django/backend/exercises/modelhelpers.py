from exercises.models import Exercise, Question, Answer
from exercises.serializers import ExerciseSerializer, AnswerSerializer
import json
from django.core.exceptions import ObjectDoesNotExist


def serialize_exercise_with_question_data(exercise, user):
    questions = Question.objects.filter(exercise=exercise)
    correct = exercise.user_is_correct(user)
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data['question'] = {}
    data['correct'] = correct
    for question in questions:
        try:
            dbanswer = Answer.objects.filter(user=user, question=question).latest('date')
            serializer = AnswerSerializer(dbanswer)
            response = json.loads(dbanswer.grader_response)
            data['question'][question.question_key] = serializer.data
            data['question'][question.question_key]['response'] = response
        except ObjectDoesNotExist:
            pass
    return data
