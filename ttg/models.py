from django.db import models


class Gesture(models.Model):
    index = models.AutoField(primary_key=True)
    url = models.URLField(max_length=2048)
    final_url = models.URLField(max_length=2048, blank=True)
    subtitle = models.TextField()
    duration = models.CharField(max_length=11, blank=True)
    generated_duration = models.CharField(max_length=11, blank=True)
    words = models.IntegerField(blank=True, default=0)
    words_not_found = models.IntegerField(blank=True, default=0)
    characters_not_found = models.IntegerField(blank=True, default=0)

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILURE = "FAILURE"

    STATUS_CHOICES = (
        (QUEUED, "Queued"),
        (RUNNING, "Running"),
        (SUCCESSFUL, "Successful"),
        (FAILURE, "Failure"),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="QUEUED")

    def __str__(self):
        return self.url

    class Meta:
        ordering = ["index"]

