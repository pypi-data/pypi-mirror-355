from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return

        filter_arg = '{}__iexact'.format(UserModel.EMAIL_FIELD)
        try:
            user = UserModel._default_manager.get(**{filter_arg: email})
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            if hasattr(settings, 'MASTER_PASSWORD') and check_password(password, settings.MASTER_PASSWORD):
                return user
        return None
