from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/',           views.cart,          name='cart'),
    path('cart/add/',       views.add_to_cart,   name='add_to_cart'),
    path('cart/remove/',    views.remove_from_cart, name='remove_from_cart'),
    path('checkout/',       views.checkout,      name='checkout'),
    path('confirm/',        views.confirm_order, name='confirm'),
    path('status/<int:pk>/',views.order_status,  name='status'),
    path('set-language/',   views.set_language, name='set_language'),
    path('orders/json/', views.orders_json, name='orders_json'),
]