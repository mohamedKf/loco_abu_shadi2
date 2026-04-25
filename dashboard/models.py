from django.db import models


class PrinterConfig(models.Model):
    """Stores printer settings — edited via dashboard settings page."""
    PRINTER_TYPES = [
        ('network', 'Network (LAN/WiFi)'),
        ('usb',     'USB'),
        ('none',    'No Printer'),
    ]

    printer_type = models.CharField(max_length=10, choices=PRINTER_TYPES, default='none')
    host         = models.CharField(max_length=100, blank=True, default='')
    port         = models.IntegerField(default=9100)
    vendor_id    = models.CharField(max_length=20, blank=True, default='0x04b8')
    product_id   = models.CharField(max_length=20, blank=True, default='0x0202')
    auto_print   = models.BooleanField(default=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Printer Config'

    def __str__(self):
        return f"Printer: {self.printer_type} — {self.host or 'USB'}"

    @classmethod
    def get(cls):
        """Always returns a config object — creates default if none exists."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RestaurantConfig(models.Model):
    """Stores restaurant info — edited via dashboard settings page."""
    name_ar  = models.CharField(max_length=100, default='LOCO Abu Shadi')
    name_he  = models.CharField(max_length=100, blank=True, default='')
    city     = models.CharField(max_length=100, blank=True, default='')
    phone    = models.CharField(max_length=30, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Restaurant Config'

    def __str__(self):
        return self.name_ar

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj