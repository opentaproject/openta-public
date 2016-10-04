from rest_framework import serializers
from exercises.models import Exercise, ExerciseMeta
from exercises.models import Question
from exercises.models import Answer


class ExerciseMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseMeta
        fields = (
            'published',
            'deadline_date',
            'pdf_solution',
            'difficulty',
            'required',
            'image',
            'bonus',
            'server_reply_time',
        )


class ExerciseSerializer(serializers.ModelSerializer):
    meta = ExerciseMetaSerializer()

    class Meta:
        model = Exercise
        fields = ('exercise_key', 'name', 'path', 'folder', 'meta')


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('exercise', 'question_id')


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('user', 'question', 'answer', 'grader_response', 'correct', 'date')
