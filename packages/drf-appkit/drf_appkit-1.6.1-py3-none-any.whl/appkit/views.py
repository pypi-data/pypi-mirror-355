from django.conf import settings
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404

# from .auth.decorators import access_token_required
from .models import (
    Attachment,
)
from .shortcuts import x_sendfile_response

@never_cache
def secure_media(request, signed_pk, *args, **kwargs):
    attachment_pk = Attachment.signer.unsign(signed_pk)
    attachment = Attachment.objects.get(pk=attachment_pk)

    attachment_path = attachment.file.name

    return x_sendfile_response(
        request,
        attachment_path,
        media_root=settings.SECURE_MEDIA_ROOT
    )
