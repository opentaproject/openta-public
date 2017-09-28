from rest_framework import serializers
from exercises.models import Exercise, ExerciseMeta
from exercises.models import Question
from exercises.models import Answer
from exercises.models import ImageAnswer
from exercises.models import AuditExercise
from exercises.models import AuditResponseFile
from course.models import Course
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


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
            'allow_pdf',
        )

    def get_deadline_time(self, obj):
        return Course.objects.deadline_time()


class ExerciseSerializer(serializers.ModelSerializer):
    meta = ExerciseMetaSerializer()

    class Meta:
        model = Exercise
        fields = ('exercise_key', 'name', 'translated_name', 'path', 'folder', 'meta')


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
        fields = ('user', 'exercise', 'pk', 'date', 'filetype')


class AuditResponseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditResponseFile
        fields = '__all__'


class AuditExerciseSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField()
    auditor_data = UserSerializer(source="auditor", read_only=True)
    responsefiles = AuditResponseFileSerializer(
        many=True
    )  # serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AuditExercise
        fields = (
            'pk',
            'student',
            'auditor',
            'auditor_data',
            'exercise',
            'date',
            'message',
            'subject',
            'sent',
            'published',
            'force_passed',
            'student_username',
            'responsefiles',
            'revision_needed',
            'updated',
            'updated_date',
        )

    def update(self, instance, validated_data):
        instance.message = validated_data.get('message', instance.message)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.published = validated_data.get('published', instance.published)
        instance.updated = validated_data.get('updated', instance.updated)
        instance.revision_needed = validated_data.get('revision_needed', instance.revision_needed)
        instance.force_passed = validated_data.get('force_passed', instance.force_passed)
        instance.save()
        return instance

    def get_student_username(self, instance):
        return instance.student.username
