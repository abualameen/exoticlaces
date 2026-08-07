from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Web3Payment
from .services import Web3PaymentService

@receiver(post_save, sender=Web3Payment)
def web3_payment_created(sender, instance, created, **kwargs):
    """Handle payment creation"""
    if created:
        print(f"🔔 Web3 Payment #{instance.id} created for order #{instance.order.id if instance.order else 'None'}")