from rest_framework import serializers
from course.models import Course


class CourseSerializer(serializers.ModelSerializer):
    languages = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'course_name',
            'published',
            'pk',
            'icon',
            'registration_password',
            'registration_by_password',
            'registration_by_domain',
            'languages',
            'difficulties',
            'email_reply_to',
            'motd',
            'url',
            'use_email'
        )

    def get_languages(self, instance):
        if instance.languages is not None:
            return list(map(str.strip, instance.languages.split(',')))
        else:
            return None


class CourseStudentSerializer(serializers.ModelSerializer):
    languages = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'course_name',
            'published',
            'icon',
            'email_reply_to',
            'pk',
            'languages',
            'motd',
            'url',
            'use_email',
        )

    def get_languages(self, instance):
        return instance.get_languages()
