from rest_framework import serializers
from course.models import Course


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'course_name',
            'registration_password',
            'registration_by_password',
            'registration_by_domain',
        )
