from django.db import models
from django.db.models.functions import Now


class Term(models.Model):
    url = models.CharField(max_length=64, unique=True, default="undefined")
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=32, null=True, blank=True)
    definition = models.TextField()
    example = models.TextField(null=True, blank=True)
    alternative_forms = models.CharField(max_length=300, null=True, blank=True)
    copyright = models.CharField(max_length=64, null=True, blank=True)
    origin = models.CharField(max_length=300, null=True, blank=True)
    date_added = models.DateTimeField(db_default=Now())
    date_edited = models.DateTimeField(db_default=Now())
    key = models.IntegerField()

    def __str__(self):
        return self.name
