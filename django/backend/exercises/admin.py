from django.contrib import admin

from .models import Exercise
from .models import Question
from .models import Answer

admin.site.register(Exercise)
admin.site.register(Question)
admin.site.register(Answer)

# Register your models here.
