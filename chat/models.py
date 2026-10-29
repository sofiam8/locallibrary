from django.conf import settings
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=50, unique=True)
    topic = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(
        Room, related_name="messages", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="chat_messages",
        on_delete=models.SET_NULL,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.author or 'anonymous'} in {self.room}: {self.content[:50]}"
