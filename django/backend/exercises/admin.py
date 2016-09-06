from django.contrib import admin

from .models import Exercise
from .models import Question
from .models import Answer
from .models import ImageAnswer

admin.site.register(Exercise)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(ImageAnswer)

# Register your models here.
