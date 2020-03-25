from django.contrib.auth.decorators import permission_required
import backend.settings as settings
from exercises.models import ExerciseMeta, Exercise
from django.views.generic.edit import UpdateView
from django import forms
from django.forms.models import modelform_factory


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
        'student_assets',
    ]

    def get_object(self, queryset=None):
        obj = self.model.objects.get(pk=self.kwargs['pk'])
        if 'difficulties' in self.kwargs:
            fields = obj._meta.fields
            difficulty = list(filter(lambda x: str(x.attname) == 'difficulty', fields))[0]
            difficulty.choices = self.kwargs['difficulties']

        return obj

    model = ExerciseMeta
    success_url = '/' + settings.SUBPATH + 'exercisemeta/{id}'


def split_or_repeat(txt):
    txt = txt.strip('\r\n')
    pieces = txt.split(':')
    print("txt = ", txt)
    if len(pieces) < 2:
        pieces = [txt, txt]
    return tuple(pieces)
    print("pices = ", pieces)


def split_or_repeat(txt):
    txt = txt.strip('\r\n')
    pieces = txt.split(':')
    print("txt = ", txt)
    if len(pieces) < 2:
        pieces = [txt, txt]
    return tuple(pieces)
    print("pices = ", pieces)


@permission_required('exercises.administer_exercise')
def ExerciseMetaUpdateView(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    meta, created = ExerciseMeta.objects.get_or_create(exercise=dbexercise)
    try:
        difficultieslist = meta.exercise.course.difficulties.split(',')
        difficulties = tuple(split_or_repeat(str(v)) for v in difficultieslist)
    except:
        difficulties = None
    # difficulties = tuple( {('B' + v, v) for k,v in enumerate( difficultieslist ) })
    result = ExerciseMetaUpdate.as_view()(request, pk=meta.id, difficulties=difficulties)
    if request.method == 'POST':
        result.set_cookie('submitted', 'true')
    else:
        result.set_cookie('submitted', 'false')

    return result
