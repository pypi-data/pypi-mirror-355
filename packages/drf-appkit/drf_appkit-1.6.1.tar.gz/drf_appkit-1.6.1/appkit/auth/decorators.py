from functools import wraps

from django.core.exceptions import PermissionDenied

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


# def access_token_required(view_func):
#     """
#     Decorator that ensures a valid access token is present in the request header
#     """
#     @wraps(view_func)
#     def _wrapped_view_func(request, *args, **kwargs):
#         access_token = request.COOKIES.get('motostar.auth.accessToken')
#         if not access_token:
#             raise PermissionDenied
#
#         jwt_authentication = JWTAuthentication()
#         try:
#             # Validate the given access token
#             jwt_authentication.get_validated_token(access_token)
#         except InvalidToken as e:
#             raise PermissionDenied
#
#         return view_func(request, *args, **kwargs)
#     return _wrapped_view_func
