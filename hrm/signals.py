from django.db.models.signals import pre_save
from django.dispatch import Signal, receiver
from django.db.models import Model
from .models import PaySlip
from django.apps import apps

# Define a custom signal
object_updated = Signal()

# Define a receiver function to check for updates and send the signal
@receiver(pre_save, sender=PaySlip)
def payroll_pre_save(sender, instance, **kwargs):
    if issubclass(sender, Model):
        if instance.pk is not None:
            object_updated.send(sender=sender, instance=instance)