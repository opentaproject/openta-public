from django.conf.urls import url
from exercises import views

urlpatterns = [url(r'^exercises/$', views.exercise_list)]
