from django.db import models
from django.db.models import CharField


class ApiModel(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self) -> CharField:
        return self.name

    class Meta:
        app_label = "api_app"
