from rest_framework.relations import RelatedField


class DocumentUUIDRelatedField(RelatedField):
    """
    A read only field that represents its targets using their
    plain string representation.
    """

    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, document):
        return str(document.uuid)