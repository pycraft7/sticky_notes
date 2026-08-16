from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    full_name = models.CharField(
        max_length=150
    )

    photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.full_name