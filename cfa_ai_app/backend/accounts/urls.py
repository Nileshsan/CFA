from django.urls import path
from .views import TransactionUploadView
from . import views

urlpatterns = [
    path('api/transactions/', TransactionUploadView.as_view(), name='receive_transactions'),
    path('api/transactions/<str:client_name>/', views.get_client_transactions, name='client_transactions'),
    path('api/transactions/', views.get_client_transactions, name='all_transactions'),
    path('api/clients/summary/', views.get_clients_summary, name='clients_summary'),
    path('api/opening-balances/', views.receive_opening_balances, name='receive_opening_balances'),
]