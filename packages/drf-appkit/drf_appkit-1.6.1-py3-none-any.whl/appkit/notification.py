import os

from django.conf import settings
from django.templatetags.static import static

from mail_templated import EmailMessage

from .shortcuts import send_sms, site_url_base

SMS_SRC_NUMBER = os.environ.get('PLIVO_SMS_SOURCE_NUMBER')


class AppkitEmailMessage(EmailMessage):
    sender = settings.DEFAULT_FROM_EMAIL_SENDER

    def __init__(self, template_name=None, site=None, context=None, *args, **kwargs):
        email_context = context or {}

        app_site_url = site_url_base(None)
        email_context.update({
            'app_name': settings.PROJECT_NAME,
            'app_site_url': app_site_url,
            'app_icon_url': f'{app_site_url}{static("images/icon/android-chrome-192x192.png")}',
        })

        if site:
            self.sender = site.name
            email_context.update({
                'site_name': site.name,
                'site_url': site_url_base(site),
            })            
            if site.profile.icon:
                email_context['site_icon_url'] = site.profile.icon_renditions['192']

        if 'sender' in kwargs:
            self.sender = kwargs.pop('sender')

        super().__init__(template_name, email_context, *args, **kwargs)

    def send(self, *args, **kwargs):
        if self.sender:
            self.from_email = f"{self.sender} <{self.from_email}>"

        self.to = list(*args)
        self.cc = kwargs.pop('cc', self.cc)
        self.bcc = kwargs.pop('bcc', self.bcc)
        self.reply_to = kwargs.pop('reply_to', self.reply_to)
                
        self.context['allow_reply'] = True if self.reply_to else False

        super(AppkitEmailMessage, self).send(*args, **kwargs)


class AppkitSMSMessage:
    def __init__(self, message, recipients, *args, **kwargs):
        self.recipients = recipients
        self.message = message

    def send(self, *args, **kwargs):
        if not self.recipients:
            return

        dst_phone = '<'.join(self.recipients)
        return send_sms(dst_phone, self.message)
