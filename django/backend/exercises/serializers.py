from rest_framework import serializers
from exercises.models import Exercise, ExerciseMeta
from exercises.models import Question
from exercises.models import Answer
from exercises.models import ImageAnswer
from exercises.models import AuditExercise
from course.models import Course


class ExerciseMetaSerializer(serializers.ModelSerializer):
    deadline_time = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseMeta
        fields = (
            'published',
            'deadline_date',
            'deadline_time',
            'solution',
            'difficulty',
            'required',
            'image',
            'bonus',
            'server_reply_time',
            'sort_key',
        )

    def get_deadline_time(self, obj):
        return Course.objects.deadline_time()


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
        fields = (
            'pk',
            'student',
            'auditor',
            'exercise',
            'date',
            'message',
            'subject',
            'sent',
            'resolved',
            'force_passed',
        )

    def update(self, instance, validated_data):
        instance.message = validated_data.get('message', instance.message)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.resolved = validated_data.get('resolved', instance.resolved)
        instance.force_passed = validated_data.get('force_passed', instance.force_passed)
        instance.save()
        return instance
