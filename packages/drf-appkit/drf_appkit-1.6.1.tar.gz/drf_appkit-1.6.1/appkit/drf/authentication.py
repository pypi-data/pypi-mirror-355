from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from ..settings import appkit_settings

get_current_site = appkit_settings.CURRENT_SITE_ACCESSOR


class JWTAuthentication(BaseJWTAuthentication):
    def authenticate(self, request):
        base_auth_result =  super().authenticate(request)
        if base_auth_result is None:
            return None

        user, validated_token = base_auth_result

        # Ensure user is a staff member within the active site
        try:
            current_site = get_current_site(request)
        except ObjectDoesNotExist:
            raise AuthenticationFailed(_('Site not found'), code='site_not_found')

        if not (user.is_staff and user.profile.site == current_site):
            raise AuthenticationFailed(_('User not found'), code='user_not_found')

        return user, validated_token
