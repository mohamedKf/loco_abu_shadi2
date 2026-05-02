from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                              views.overview,          name='overview'),
    path('orders/',                       views.orders_list,       name='orders'),
    path('orders/<int:pk>/',              views.order_detail,      name='order_detail'),
    path('menu/',                         views.menu_management,   name='menu'),
    path('menu/item/add/',                views.item_add,          name='item_add'),
    path('menu/item/<int:pk>/edit/',      views.item_edit,         name='item_edit'),
    path('menu/item/<int:pk>/delete/',    views.item_delete,       name='item_delete'),
    path('menu/item/<int:pk>/toggle/',    views.item_toggle,       name='item_toggle'),
    path('menu/category/',               views.category_list,     name='categories'),
    path('menu/category/<int:pk>/edit/', views.category_edit,     name='category_edit'),
    path('menu/category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('menu/topping/',                views.topping_list,      name='toppings'),
    path('menu/topping/<int:pk>/edit/',  views.topping_edit,      name='topping_edit'),
    path('menu/topping/<int:pk>/delete/', views.topping_delete,   name='topping_delete'),
    path('menu/topping/<int:pk>/toggle/', views.topping_toggle,   name='topping_toggle'),
    path('tables/',                       views.tables_management, name='tables'),
    path('tables/add/',                   views.table_add,         name='table_add'),
    path('tables/<int:pk>/qr/',           views.table_qr,          name='table_qr'),
    path('tables/<int:pk>/delete/',       views.table_delete,      name='table_delete'),
    path('reports/',                      views.reports,           name='reports'),
    path('reports/export/',               views.export_csv,        name='export_csv'),
    path('orders/<int:pk>/receipt/', views.order_receipt_pdf, name='order_receipt'),
    path('printer/test/', views.printer_test, name='printer_test'),
    path('settings/',                     views.site_settings,     name='settings'),

    path('menu/topping/group/<int:pk>/edit/',   views.topping_group_edit,   name='topping_group_edit'),
    path('menu/topping/group/<int:pk>/delete/', views.topping_group_delete, name='topping_group_delete'),
]