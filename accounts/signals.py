from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Merchant


@receiver(post_save, sender=User)
def create_merchant(sender, instance, created, **kwargs):
    if created:
        Merchant.objects.create(user=instance)
