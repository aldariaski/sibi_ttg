from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_gesture', views.add_gesture, name='request_gesture'),
    path('get_task', views.get_task, name='get_task'),
    path('get_gesture', views.get_gesture, name='get_gesture'),
    path('get_running_gesture', views.get_running_gesture, name='get_running_gesture'),
    path('get_queued_gesture', views.get_queued_gesture, name='get_queued_gesture'),
    path('get_successful_gesture', views.get_successful_gesture, name='get_successful_gesture'),
    path('get_failure_gesture', views.get_failure_gesture, name='get_failure_gesture'),
]