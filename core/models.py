# core/models.py
from django.db import models

class LaunchWaitlist(models.Model):
    name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50, blank=True, help_text="utm/source éventuelle")

    def __str__(self):
        return self.email
