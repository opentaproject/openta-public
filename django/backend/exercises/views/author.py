from django.contrib.auth.decorators import permission_required
import backend.settings as settings
from exercises.models import ExerciseMeta, Exercise
from django.views.generic.edit import UpdateView


class ExerciseMetaUpdate(UpdateView):
    model = ExerciseMeta
    fields = [
        'deadline_date',
        'solution',
        'difficulty',
        'required',
        'bonus',
        'image',
        'allow_pdf',
        'published',
        'sort_key',
        'feedback',
    ]
    success_url = '/' + settings.SUBPATH + 'exercisemeta/{id}'


@permission_required('exercises.administer_exercise')
def ExerciseMetaUpdateView(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    meta, created = ExerciseMeta.objects.get_or_create(
        exercise=dbexercise, defaults={'exercise_key': exercise}
    )
    result = ExerciseMetaUpdate.as_view()(request, pk=meta.id)
    if request.method == 'POST':
        result.set_cookie('submitted', 'true')
    else:
        result.set_cookie('submitted', 'false')

    return result
