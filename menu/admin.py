from django.contrib import admin
from .models import Category, MenuItem, Topping, ToppingGroup


@admin.register(ToppingGroup)
class ToppingGroupAdmin(admin.ModelAdmin):
    list_display  = ['name_ar', 'icon', 'sort_order']
    list_editable = ['sort_order']


@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display  = ['name_ar', 'group', 'price', 'is_available']
    list_editable = ['price', 'is_available']
    list_filter   = ['group']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name_ar', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ['name_ar', 'category', 'price', 'is_available', 'sort_order']
    list_editable = ['price', 'is_available', 'sort_order']
    list_filter   = ['category', 'is_available']
    filter_horizontal = ['toppings']