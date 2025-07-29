from django.contrib.auth.tokens import default_token_generator

from djoser import utils as djoser_utils
from djoser.conf import settings as djoser_settings

from ..email import AppkitEmailMessage


class ActivationEmail(AppkitEmailMessage):
    def __init__(self, request, context=dict, *args, **kwargs):
        user = context.get('user')

        email_context = dict(context)
        email_context.update({
            'request': request,
            'uid': djoser_utils.encode_uid(user.pk),
            'token': default_token_generator.make_token(user),
        })
        url = djoser_settings.ACTIVATION_URL.format(**email_context)
        email_context['url'] = url

        super().__init__("email/activation.mjml", email_context, *args, **kwargs)

    def send(self, to, *args, **kwargs):
        self.to = to
        super().send(*args, **kwargs)


class PasswordResetEmail(AppkitEmailMessage):
    def __init__(self, request, context=dict, *args, **kwargs):
        user = context.get('user')

        email_context = dict(context)
        email_context.update({
            'request': request,
            'uid': djoser_utils.encode_uid(user.pk),
            'token': default_token_generator.make_token(user),
        })
        url = djoser_settings.PASSWORD_RESET_CONFIRM_URL.format(**email_context)
        email_context['url'] = url

        super().__init__("email/password_reset.mjml", email_context, *args, **kwargs)

    def send(self, to, *args, **kwargs):
        self.to = to
        super().send(*args, **kwargs)
