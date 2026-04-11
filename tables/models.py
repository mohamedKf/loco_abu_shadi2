import uuid
from django.db import models


class Table(models.Model):
    number    = models.PositiveIntegerField(unique=True)
    qr_token  = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Table {self.number}"

    def get_qr_url(self):
        return f"/table/{self.qr_token}/"
