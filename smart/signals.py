from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import *






User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
        
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
        
        
@receiver(post_save, sender=User)
def assign_default_package(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and not instance.package:
        try:
            default_package = Package.objects.get(package_id='001')
            instance.package = default_package
            instance.save()
        except Package.DoesNotExist:
            pass
        
    
@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    if created:
        OrderNotification.objects.create(order=instance)