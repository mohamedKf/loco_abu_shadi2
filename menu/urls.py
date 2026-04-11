from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('',              views.home,        name='home'),
    path('menu/<int:pk>/', views.item_detail, name='item_detail'),
]