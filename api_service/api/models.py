from django.conf import settings
from django.db import models
from django.utils import timezone


class UserRequestHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.JSONField(null=True, blank=True)  # For storing raw API response
    
    class Meta:
        verbose_name_plural = "User request histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.symbol} at {self.date}"