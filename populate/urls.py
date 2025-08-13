from django.urls import path

from . import views

urlpatterns = [
    path('<str:siteid>/item/sales/<str:date>/', views.populate_data, name='populate_data'),
    path('ism/<str:siteid>/<str:date>/', views.ism_data, name='ism_data'),
    path('<str:siteid>/report-exported/<str:date>/', views.populate_report_exported, name='populate_report_exported'),
    path('itemized-inventory/<str:siteid>/<str:date>/', views.itemized_inventory, name='itemized_inventory')
]