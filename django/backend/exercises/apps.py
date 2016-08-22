from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    name = 'exercises'

    def ready(self):
        from .models import Exercise

        Exercise.objects.sync_with_disc()
