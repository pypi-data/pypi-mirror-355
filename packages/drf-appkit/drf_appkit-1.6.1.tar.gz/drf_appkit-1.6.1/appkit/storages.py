from django.conf import settings

from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_STORAGE_BUCKET_NAME

    def __init__(self, **settings):
        super().__init__(**settings)
        self.custom_domain = self.bucket_name
