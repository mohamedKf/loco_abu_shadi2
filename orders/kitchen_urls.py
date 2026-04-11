from django.urls import path
from . import kitchen_views

urlpatterns = [
    path('',                    kitchen_views.kitchen_display, name='kitchen'),
    path('update/<int:pk>/',    kitchen_views.update_status,   name='kitchen_update'),
    path('orders/',             kitchen_views.worker_orders,   name='worker_orders'),
]