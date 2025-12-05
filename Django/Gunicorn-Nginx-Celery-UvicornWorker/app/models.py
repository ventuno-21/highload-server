from django.db import models
from django.contrib.auth.models import AbstractUser


class Item(models.Model):
    name = models.CharField(max_length=255)
    value = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class RequestLog(models.Model):
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status = models.IntegerField()
    duration_ms = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.path}"
