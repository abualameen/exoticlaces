# lacesstore/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User


@receiver(post_save, sender=EmailAddress)
def activate_user_on_email_confirm(sender, instance, created, **kwargs):
    """
    When a user confirms their email via allauth, automatically activate them.
    """
    if instance.verified and not instance.user.is_active:
        # User has confirmed email, activate them
        instance.user.is_active = True
        instance.user.save()
        print(f"✅ User {instance.user.username} activated after email confirmation")