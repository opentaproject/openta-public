from rest_framework import serializers
from exercises.models import Exercise, ExerciseMeta
from exercises.models import Question
from exercises.models import Answer
from exercises.models import ImageAnswer
from exercises.models import AuditExercise


class ExerciseMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseMeta
        fields = (
            'published',
            'deadline_date',
            'solution',
            'difficulty',
            'required',
            'image',
            'bonus',
            'server_reply_time',
            'sort_key',
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


class ImageAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAnswer
        fields = ('user', 'exercise', 'pk', 'date')


class AuditExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditExercise
        fields = ('pk', 'student', 'auditor', 'exercise', 'date', 'message', 'sent')

    def update(self, instance, validated_data):
        instance.message = validated_data.get('message', instance.message)
        instance.save()
        return instance
