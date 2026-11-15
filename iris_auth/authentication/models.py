# authentication/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    iris_image = models.ImageField(upload_to='iris_images/', null=True, blank=True)
    user_id_1 = models.IntegerField(null=True, blank=True)  # First ID
    user_id_2 = models.IntegerField(null=True, blank=True)  # Second ID
    image_1 = models.ImageField(upload_to='iris_images/', null=True, blank=True)  # Placeholder for picture
    percentage_1 = models.FloatField(null=True, blank=True)  # Placeholder for percentage
    # percentage_2 = models.FloatField(null=True, blank=True)  # Placeholder for percentage

    def save(self, *args, **kwargs):
        # Assign two unique IDs based on existing users in the database
        if not self.user_id_1 and not self.user_id_2:
            last_user = CustomUser.objects.order_by('-pk').first()  # Get the last created user
            if last_user:
                self.user_id_1 = last_user.user_id_2 + 1
                self.user_id_2 = self.user_id_1 + 1
            else:
                # Assign the first two IDs if this is the first user
                self.user_id_1 = 0
                self.user_id_2 = 1
        super(CustomUser, self).save(*args, **kwargs)
