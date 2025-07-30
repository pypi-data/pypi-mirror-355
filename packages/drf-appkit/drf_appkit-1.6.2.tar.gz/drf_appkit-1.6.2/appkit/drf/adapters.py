from drf_auto_endpoint.adapters import BaseAdapter


class AppkitAdapter(BaseAdapter):
    @classmethod
    def adapt_field(cls, field):
        return super().adapt_field(field)
