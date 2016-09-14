from exercises.models import Exercise, ExerciseMeta, Question, Answer
from exercises.serializers import ExerciseSerializer, ExerciseMetaSerializer, AnswerSerializer
import json
from django.core.exceptions import ObjectDoesNotExist
import os
from functools import reduce


def exercise_folder_structure(manager, user):
    folders = {}
    exercises = manager.all()
    paths = map(lambda x: os.path.dirname(x.path), exercises)
    unique_paths = filter(lambda x: x != '/', set(paths))
    for path in list(map(lambda x: x.split('/')[1:], unique_paths)):
        traverse = folders
        for folder in path:
            if not ('folders' in traverse):
                traverse['folders'] = {}
            if folder in traverse['folders']:
                traverse = traverse['folders'][folder]['content']
            else:
                traverse['folders'][folder] = {'content': {}}
    for exercise in exercises:
        # If this becomes a speed issue this should be done by getting all the answers and then populating the tree
        allcorrect = True
        questions = Question.objects.filter(exercise=exercise)
        print("Exercise: " + str(exercise) + " " + str(questions.count()))
        for question in questions:
            try:
                answer = Answer.objects.filter(user=user, question=question).latest('date')
                print("dbcorrect: " + str(answer.correct))
                if not answer.correct:
                    allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
            print(allcorrect)
        paths = list(filter(lambda x: x != '', exercise.path.split('/')[1:-1]))
        root = reduce(lambda a, b: a['folders'].get(b)['content'], paths, folders)
        if 'exercises' not in root:
            root['exercises'] = {}
        root['exercises'].update(
            {
                exercise.exercise_key: {
                    'name': exercise.name,
                    'correct': allcorrect,
                    'meta': ExerciseMetaSerializer(exercise.meta).data
                    if hasattr(exercise, 'meta')
                    else {},
                }
            }
        )
    return folders


def serialize_exercise_with_question_data(exercise, user):
    questions = Question.objects.filter(exercise=exercise)
    correct = exercise.user_is_correct(user)
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data['question'] = {}
    data['correct'] = correct
    # try:
    #    meta = ExerciseMeta.objects.get(exercise=exercise)
    #    metaser = ExerciseMetaSerializer(meta)
    #    data['meta'] = metaser.data
    # except ObjectDoesNotExist:
    #    pass
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
