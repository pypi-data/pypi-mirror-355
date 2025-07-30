from django import apps

class AppConfig(apps.AppConfig):
    name = 'appkit'
    verbose_name = 'AppKit'

    def ready(self):
        # Makes sure all signal handlers are connected
        from . import handlers  # noqa