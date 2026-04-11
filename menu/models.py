from django.db import models


class Category(models.Model):
    name       = models.CharField(max_length=100)
    name_ar    = models.CharField(max_length=100)
    name_he    = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name_ar


class ToppingGroup(models.Model):
    """Category group for toppings — e.g. Bread Spreads, Vegetables, Sauces, Extras"""
    name       = models.CharField(max_length=100)
    name_ar    = models.CharField(max_length=100)
    name_he    = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    icon       = models.CharField(max_length=10, blank=True, default='🥗')

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name_ar


class Topping(models.Model):
    group        = models.ForeignKey(ToppingGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='toppings')
    name         = models.CharField(max_length=100)
    name_ar      = models.CharField(max_length=100)
    name_he      = models.CharField(max_length=100, blank=True)
    price        = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)
    sort_order   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name_ar


class MenuItem(models.Model):
    category     = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name         = models.CharField(max_length=150)
    name_ar      = models.CharField(max_length=150)
    name_he      = models.CharField(max_length=150, blank=True)
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    image        = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    sort_order   = models.PositiveIntegerField(default=0)
    toppings     = models.ManyToManyField('Topping', blank=True, related_name='menu_items')
    # Detail page fields
    description  = models.TextField(blank=True)
    calories     = models.PositiveIntegerField(null=True, blank=True)
    protein      = models.PositiveIntegerField(null=True, blank=True)
    carbs        = models.PositiveIntegerField(null=True, blank=True)
    fat          = models.PositiveIntegerField(null=True, blank=True)
    allergens    = models.CharField(max_length=255, blank=True)
    is_spicy     = models.BooleanField(default=False)
    is_new       = models.BooleanField(default=False)
    # Weight-based selling (e.g. mortadella)
    sold_by_weight = models.BooleanField(default=False)
    weight_unit    = models.CharField(
        max_length=10,
        choices=[('gram', 'גרם / غرام'), ('100g', '100 גרם'), ('kg', 'ק"ג / كيلو')],
        default='100g',
        blank=True
    )
    price_per_unit = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="السعر لكل وحدة (100g/kg) — اتركه فارغاً إذا كان السعر ثابت"
    )

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name_ar} — ₪{self.price}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('menu:item_detail', kwargs={'pk': self.pk})