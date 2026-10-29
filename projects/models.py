
from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Role(models.TextChoices):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Membership(models.Model):
    project = models.ForeignKey(
        Project,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        max_length=10,
        choices=Role,
        default=Role.MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.project} ({self.role})"


class Label(models.Model):
    project = models.ForeignKey(
        Project,
        related_name="labels",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#808080")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
