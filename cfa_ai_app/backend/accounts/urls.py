from django.urls import path
from . import views

urlpatterns = [
    path('api/transactions/', views.receive_tally_transactions, name='receive_transactions'),
    path('api/transactions/<str:client_name>/', views.get_client_transactions, name='client_transactions'),
    path('api/transactions/', views.get_client_transactions, name='all_transactions'),
    path('api/clients/summary/', views.get_clients_summary, name='clients_summary'),
] 