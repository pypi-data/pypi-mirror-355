import unicodecsv as csv

from six import BytesIO
from django.conf import settings

from rest_framework_csv.renderers import CSVRenderer

from ..util import value_for_key_path


class ExportRenderer(CSVRenderer):
    model_class = None
    field_arrangement = None

    def render_cell(self, instance, record, key):
        accessor_name = 'get_{}'.format(key)
        accessor = getattr(self, accessor_name, None)
        if accessor:
            return accessor(instance, record)

        try:
            return value_for_key_path(record, key, '')
        except KeyError:
            return value_for_key_path(instance, key, '')

    def render_row(self, instance, record):
        row = []
        for field_info in self.field_arrangement:
            key = field_info['key']
            value = self.render_cell(instance, record, key)
            row.append(value)
        return row


    def render(self, data, media_type=None, renderer_context=dict, writer_opts=None):
        if not self.field_arrangement:
            return super().render(data, media_type, renderer_context, writer_opts)

        encoding = renderer_context.get('encoding', settings.DEFAULT_CHARSET)
        writer_opts = renderer_context.get('writer_opts', writer_opts or self.writer_opts or {})

        rows = []
        for record in data:
            instance = self.model_class.objects.get(pk=record['id'])
            rows.append(self.render_row(instance, record))

        csv_buffer = BytesIO()
        csv_writer = csv.writer(csv_buffer, encoding=encoding, **writer_opts)

        csv_writer.writerow([field_info['label'] for field_info in self.field_arrangement])

        if hasattr(self, 'header_row'):
            csv_writer.writerow(self.header_row(data, rows))

        for row in rows:
            csv_writer.writerow(row)

        if hasattr(self, 'footer_row'):
            csv_writer.writerow(self.footer_row(data, rows))

        return csv_buffer.getvalue()
