from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger()
class Mailer:

    def __init__(self, subject, message, email_to):
        self.subject = subject
        self.message = message
        self.email_from = settings.EMAIL_HOST_USER
        if type(email_to) == str:
            self.email_to = [email_to]
        else:
            self.email_to = email_to

    
    def send(self, attachement=None):
        email = EmailMessage(
        self.subject,
        self.message,
        self.email_from,
        self.email_to,
        )
        if attachement:
            email.attach_file(attachement)
        try:
            email.send(
            fail_silently=True,
        )
        except Exception as e:
            logger.error(str(e))
