from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('<uuid:token>/', views.scan_qr, name='scan_qr'),
]
