from rest_framework import serializers
from exercises.models import Exercise
from exercises.models import Question


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ('exercise_key', 'name', 'path', 'folder')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('exercise', 'question_id')
