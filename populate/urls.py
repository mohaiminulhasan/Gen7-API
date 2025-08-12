from django.urls import path

from . import views

urlpatterns = [
    path('<str:siteid>/item/sales/<str:date>/', views.populate_data, name='populate_data'),
    path('ism/<str:siteid>/<str:date>/', views.ism_data, name='ism_data'),
]