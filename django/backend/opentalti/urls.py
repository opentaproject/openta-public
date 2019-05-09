from django.conf.urls import url
from . import views

app_name = "django_lti_auth"

urlpatterns = [
    url(r"^change_password/", views.change_password, name="change_password"),
    url(r"^edit_profile/", views.edit_profile, name="edit_profile"),
    url(r"^lti/$", views.lti_main),
    url(r"^lti/config_xml/$", views.config_xml),
    url(r"^(?P<course_pk>[0-9]+)/lti/$", views.lti_main),
    url(r"^(?P<course_name>[\w\.-]+)/lti/config_xml/?$", views.config_xml),
]
