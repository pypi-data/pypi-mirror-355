from django.dispatch import receiver
from .models import document_event

@receiver(document_event, sender=None)
def document_event_signal_receiver(sender, type, **kwargs):
    """
    Send notification email to users subscribed and/or concerned with the event
    of "type" that occurred on the given sender (Document)
    """
    sender.notify_users(type, **kwargs)
