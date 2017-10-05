from django.conf.urls import url, include
from .views import get_current_course

urlpatterns = [url(r'^course/', get_current_course)]
