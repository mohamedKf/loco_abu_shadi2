from django.contrib import admin
from .models import Order, OrderItem, Receipt

class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0
    readonly_fields = ['unit_price', 'get_subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ['id', 'table', 'status', 'payment_method', 'payment_status', 'total_price', 'created_at']
    list_filter    = ['status', 'payment_method', 'payment_status']
    list_editable  = ['status', 'payment_status']
    inlines        = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at', 'total_price']

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'order', 'generated_at', 'printed']
