from django.urls import path

from . import views

urlpatterns = [
    path('', views.populate_data, name='populate_data'),
]