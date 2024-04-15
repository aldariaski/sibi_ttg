from django.contrib import admin
from django_q.models import Task
from . import models


class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "started", "stopped", "time_taken", "success")

    def has_add_permission(self, request):
        """Don't allow adds."""
        return False

    search_fields = ("name", "id")


class GestureAdmin(admin.ModelAdmin):
    list_display = ("index", "url", "status")
    readonly_fields = ("url", "final_url", "subtitle", "status", "duration", "generated_duration", "words", "words_not_found", "characters_not_found")

    def has_add_permission(self, request):
        """Don't allow adds."""
        return False


admin.site.register(Task, TaskAdmin)
admin.site.register(models.Gesture, GestureAdmin)