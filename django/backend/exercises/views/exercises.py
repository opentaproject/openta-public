from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import permission_required
from exercises.models import Exercise, ExerciseMeta
from exercises.parsing import list_history
from course.models import Course
import exercises.parsing as parsing
import os, re
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_required('exercises.edit_exercise')
def exercises_add(request):
    try:
        course_pk = request.data.get('course_pk')
        dbcourse = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error('Requested course does not exist pk: %d', course_pk)
        return Response({'error': 'Invalid course'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    path = os.path.join(*request.data.get('path').split('/'))
    name = request.data.get('name')
    name = re.sub('[^\w]','',name) # MAKE SURE ONLY SIMPLY PARSED FILENAMES ARE CREATED
    res = parsing.exercise_add(os.path.join(dbcourse.get_exercises_path(), path), name)
    if 'error' in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    msg = Exercise.objects.add_exercise_full_path(res['path'], dbcourse)
    logger.info('Added exercise at ' + res['path'])
    logger.info(msg)
    return Response({'success': 'Added exercise', 'messages': msg})


@api_view(['DELETE'])
@permission_required('exercises.edit_exercise')
def exercise_delete(request, exercise):
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.error('Tried to delete invalid exercise ' + exercise)
        return Response({'error': 'Invalid exercise'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    res = parsing.exercise_delete(
        dbexercise.course.get_exercises_path(), dbexercise.get_full_path()
    )
    ExerciseMeta.objects.filter(exercise=dbexercise).update(published=False)
    if 'error' in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.info('Deleted exercise at ' + dbexercise.name)
    Exercise.objects.add_exercise('/' + res['path'], dbexercise.course)
    return Response({'success': 'Deleted exercise'})


@api_view(['POST'])
@permission_required('exercises.edit_exercise')
def exercise_move(request, exercise):
    new_folder = request.data.get('new_folder')
    new_folder = re.sub('[^\w\ :]','',new_folder)
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.error('Tried to move invalid exercise ' + exercise)
        return Response({'error': 'Invalid exercise'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    new_full_path = os.path.join(
        dbexercise.course.get_exercises_path(), *new_folder.split('/'), dbexercise.name
    )
    res = parsing.exercise_move(dbexercise.get_full_path(), new_full_path)
    if 'error' in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    Exercise.objects.add_exercise_full_path(res['path'], dbexercise.course)
    logger.info('Moved exercise ' + dbexercise.name + " to " + res['path'])
    return Response({'success': 'Moved exercise'})


@api_view(['POST'])
@permission_required('exercises.edit_exercise')
def exercises_move_folder(request):
    old_folder = request.data.get('old_folder')
    new_folder = request.data.get('new_folder')
    new_folder = re.sub('[^\w\ :]','',new_folder)
    dbexercises = Exercise.objects.filter(folder=old_folder) | Exercise.objects.filter(
        folder__startswith=old_folder + '/'
    )
    if dbexercises.count() == 0:
        return Response(
            {'error': 'There are no exercises in that folder'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    course_path = dbexercises[0].course.get_exercises_path()
    old_full_path = os.path.join(course_path, old_folder)
    new_full_path = os.path.join(course_path, new_folder)
    res = parsing.exercises_move_folder(old_full_path, new_full_path)
    if 'error' in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    for exercise_data in res['exercises']:
        Exercise.objects.add_exercise_full_path(exercise_data['path'], dbexercises[0].course)
        logger.info('Moved exercise ' + exercise_data['name'] + " to " + exercise_data['path'])
    return Response({'success': 'Moved exercise'})


@api_view(['POST'])
@permission_required('exercises.edit_exercise')
def exercises_rename_folder(request):
    old_folder = request.data.get('old_folder')
    new_name = request.data.get('new_name')
    new_name = re.sub('[^\w\ :]','',new_name)
    new_folder_list = old_folder.split('/')[:-1] + [new_name]
    new_folder = "/".join(new_folder_list)
    dbexercises = Exercise.objects.filter(folder=old_folder) | Exercise.objects.filter(
        folder__startswith=old_folder + '/'
    )
    if dbexercises.count() == 0:
        return Response(
            {'error': 'There are no exercises in that folder'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    course_path = dbexercises[0].course.get_exercises_path()
    old_full_path = os.path.join(course_path, old_folder)
    new_full_path = os.path.join(course_path, new_folder)
    res = parsing.exercises_move_folder(old_full_path, new_full_path)
    if 'error' in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    for exercise_data in res['exercises']:
        Exercise.objects.add_exercise_full_path(exercise_data['path'], dbexercises[0].course)
        logger.info('Moved exercise ' + exercise_data['name'] + " to " + exercise_data['path'])
    return Response({'success': 'Moved exercise'})


@api_view(['GET'])
@permission_required('exercises.edit_exercise')
def exercise_history(request, exercise):
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.error('Tried to access history for invalid exercise ' + exercise)
        return Response({'error': 'Invalid exercise'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(list_history(dbexercise.get_full_path()))


@api_view(['GET'])
@permission_required('exercises.edit_exercise')
def exercise_xml_history(request, exercise, name):
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.error('Tried to access history for invalid exercise ' + exercise)
        return Response({'error': 'Invalid exercise'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(parsing.exercise_xml_history(dbexercise.get_full_path(), name))


@api_view(['GET'])
@permission_required('exercises.edit_exercise')
def exercise_json_history(request, exercise, name):
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.error('Tried to access history for invalid exercise ' + exercise)
        return Response({'error': 'Invalid exercise'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(parsing.exercise_json_history(dbexercise.get_full_path(), name))
