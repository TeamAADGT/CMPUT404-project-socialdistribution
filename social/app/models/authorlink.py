from django.db import models


class AuthorLink(models.Model):
    uri = models.URLField(unique=True)
