from django.contrib import admin

from .models import Exercise
from .models import Question
from .models import Answer
from .models import ImageAnswer

from .models import ExerciseMeta


class ImageAnswerAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)


admin.site.register(Exercise)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(ImageAnswer, ImageAnswerAdmin)
admin.site.register(ExerciseMeta)

# Register your models here.
