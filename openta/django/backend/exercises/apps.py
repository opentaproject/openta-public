# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    name = "exercises"

    def ready(self):
        import exercises.questiontypes

        pass
        # from .models import Exercise
        # Exercise.objects.sync_with_disc()
