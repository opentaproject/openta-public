# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from rest_framework import serializers
from django.conf import settings
from django.core.cache import caches
from course.models import Course
import os


class CourseSerializer(serializers.ModelSerializer):
    languages = serializers.SerializerMethodField()
    motd = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    use_invitations = serializers.SerializerMethodField()
    use_chatgpt = serializers.SerializerMethodField()
    use_bugreport = serializers.SerializerMethodField()
    use_email =  serializers.SerializerMethodField()
    use_autotranslations =  serializers.SerializerMethodField()


    class Meta:
        model = Course
        fields = (
            "course_name",
            "published",
            "pk",
            "registration_password",
            "registration_by_password",
            "registration_by_domain",
            "languages",
            "difficulties",
            "email_reply_to",
            "motd",
            "url",
            "use_auto_translation",
            "use_email",
            "use_lti",
            "subdomain",
            "description",
            "icon",
            "use_invitations",
            "use_chatgpt", 
            "use_bugreport",
            "use_email",
            "use_autotranslations",
        )

    def get_use_autotranslations( self, instance ):
        return settings.USE_AUTOTRANSLATIONS

    def get_use_email( self, instance ):
        return settings.USE_EMAIL

    def get_use_invitations( self, instance ):
        return settings.USE_INVITATIONS

    def get_use_chatgpt( self, instance ) :
        return settings.USE_CHATGPT

    def get_use_bugreport( self, instance ) :
        return settings.USE_BUGREPORT

    def get_languages(self, instance):
        try :
            if not settings.RUNTESTS and caches["default"].get("temporarily_block_translations" ):
                return None
            elif instance.languages is not None:
                return list(map(str.strip, instance.languages.split(",")))
            else:
                return None
        except :
            return None

    def get_motd(self, instance):
        motd = instance.motd
        if os.path.exists("/subdomain-data/auth/motds/all"):
            fp = open("/subdomain-data/auth/motds/all")
            motd = fp.read() + motd
        baseserver = settings.BASE_SERVER
        if os.path.exists(f"/subdomain-data/auth/motds/{baseserver}-motd"):
            fp = open(f"/subdomain-data/auth/motds/{baseserver}-motd")
            motd = fp.read() + motd
        return motd

    def get_description(self, instance):
        # print(f"SUBDOMAIN = {instance.subdomain}")
        opentasite = instance.opentasite
        data = instance.data
        try:
            description = data.get("description", "No course description is available")
        except Exception as e:
            description = "No course description is available"
        return description


class CourseStudentSerializer(serializers.ModelSerializer):
    languages = serializers.SerializerMethodField()
    motd = serializers.SerializerMethodField()


    class Meta:
        model = Course
        fields = (
            "course_name",
            "published",
            "icon",
            "email_reply_to",
            "pk",
            "languages",
            "motd",
            "url",
            "use_email",
            "use_auto_translation",
            "subdomain",
            "icon",
        )

    def get_languages(self, instance):
        return instance.get_languages()


    def get_motd(self, instance):
        motd = instance.motd
        if os.path.exists("/subdomain-data/auth/motds/all"):
            fp = open("/subdomain-data/auth/motds/all")
            motd = fp.read() + motd
        baseserver = settings.BASE_SERVER
        if baseserver and os.path.exists(f"/subdomain-data/auth/motds/{baseserver}-motd"):
            fp = open(f"/subdomain-data/auth/motds/{baseserver}-motd")
            motd = fp.read() + motd
        return motd


