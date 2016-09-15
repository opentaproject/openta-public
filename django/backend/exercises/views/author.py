from django.http import FileResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
import backend.settings as settings

from exercises.models import ExerciseMeta, Exercise

from django.views.generic.edit import UpdateView


class ExerciseMetaUpdate(UpdateView):
    model = ExerciseMeta
    fields = [
        'deadline_date',
        'pdf_solution',
        'difficulty',
        'required',
        'bonus',
        'server_reply_time',
        'image',
    ]
    success_url = '/exercisemeta/{id}'  # reverse_lazy('exercise-meta-update')


def ExerciseMetaUpdateView(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    meta, created = ExerciseMeta.objects.get_or_create(
        exercise=dbexercise, defaults={'exercise_key': exercise}
    )
    print(request.POST)
    result = ExerciseMetaUpdate.as_view()(request, pk=meta.id)
    print(result)
    if request.method == 'POST':
        result.set_cookie('submitted', 'true')
    else:
        result.set_cookie('submitted', 'false')

    return result
