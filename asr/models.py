from django.db import models

class Subtitle(models.Model):
    index = models.AutoField(primary_key=True)
    url = models.URLField(max_length=2048)
    subtitle = models.TextField()
    asrtype = models.CharField(max_length=10, blank=True)
    duration = models.CharField(max_length=1000, blank=True)

    class Meta:
        ordering = ["index"]