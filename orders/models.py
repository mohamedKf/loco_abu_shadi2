from django.db import models
from menu.models import MenuItem, Topping
from tables.models import Table


class Order(models.Model):
    STATUS_CHOICES = [
        ('new',         'New'),
        ('in_progress', 'In Progress'),
        ('ready',       'Ready'),
        ('done',        'Done'),
        ('cancelled',   'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash',         'Cash'),
        ('cashier_card', 'Card at Cashier'),
        ('online',       'Online'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid',    'Paid'),
    ]

    table          = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='orders')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_price    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_name  = models.CharField(max_length=150, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    language       = models.CharField(max_length=5, default='ar', choices=[('ar','Arabic'),('he','Hebrew'),('en','English')])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — Table {self.table} — {self.status}"

    def calculate_total(self):
        total = sum(item.get_subtotal() for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])
        return total


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item  = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    notes      = models.TextField(blank=True)
    toppings   = models.ManyToManyField(Topping, blank=True)
    weight_grams = models.PositiveIntegerField(null=True, blank=True)  # for weight-based items

    def __str__(self):
        return f"{self.quantity}x {self.menu_item}"

    def get_subtotal(self):
        topping_total = sum(float(t.price) for t in self.toppings.all())
        if self.weight_grams and self.menu_item and self.menu_item.sold_by_weight:
            # price per 100g * (weight / 100)
            base = float(self.unit_price) * (self.weight_grams / 100)
        else:
            base = float(self.unit_price) * self.quantity
        return round(base + topping_total * self.quantity, 2)


class Receipt(models.Model):
    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=30, unique=True)
    generated_at   = models.DateTimeField(auto_now_add=True)
    printed        = models.BooleanField(default=False)

    def __str__(self):
        return self.receipt_number

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from django.utils import timezone
            year  = timezone.now().year
            count = Receipt.objects.filter(generated_at__year=year).count() + 1
            self.receipt_number = f"RCP-{year}-{count:04d}"
        super().save(*args, **kwargs)