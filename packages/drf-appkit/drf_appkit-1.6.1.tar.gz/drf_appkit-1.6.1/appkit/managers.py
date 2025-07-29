from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction


class DocumentManager(models.Manager):
    # --------------------------------------------------------------------------
    # Document Duplicating
    def post_process_duplicated_document(self, document):
        return document


    def duplicate(self, document):
        DocumentClass = self.model
        model_fields = DocumentClass._meta.get_fields()

        with transaction.atomic():
            duplicated_document = document.clone()

            generic_relation_field_names = set()
            foreign_key_relation_field_names = set()

            for field in model_fields:
                field_name = field.name
                if isinstance(field, GenericRelation):
                    generic_relation_field_names.add(field_name)
                    continue
                elif  field.one_to_many:
                    if field.related_name:
                        foreign_key_relation_field_names.add(field.related_name)
                    else:
                        foreign_key_relation_field_names.add('{}_set'.format(field_name))
                    continue
                if field.auto_created or field.many_to_many or field.one_to_one:
                    continue

            # Duplicate the one-to-many relations
            for field_name in foreign_key_relation_field_names:
                duplicated_fk_relation = getattr(duplicated_document, field_name)
                fk_related_record_manager = getattr(document, field_name)
                for item in fk_related_record_manager.all():
                    # Create a copy of the related item and add it to the
                    # foreign-key relation
                    duplicated_fk_relation.add(item.clone())

            # Duplicate the M2M relation
            for field in model_fields:
                if field.many_to_many:
                    field_name = field.name
                    related_record_manager = getattr(document, field_name)
                    duplicated_related_records = getattr(duplicated_document, field_name)
                    related_records = related_record_manager.all()
                    duplicated_related_records.add(*related_records)

            return self.post_process_duplicated_document(duplicated_document)


    # --------------------------------------------------------------------------
    # Document Merging
    # --------------------------------------------------------------------------
    @staticmethod
    def longest(a, b):
        return a if len(a) >= len(b) else b

    @staticmethod
    def concat(a, b):
        return '{}\n\n\n{}'.format(a, b)

    def create_merged_document(self, documents):
        return self.model()

    def post_process_merged_document(self, document):
        return document

    def merge(self, records):
        DocumentClass = self.model
        model_fields = DocumentClass._meta.get_fields()

        merge_strategy = DocumentClass.merge_strategy()
        """
        For Fields:
        1) If a field value exists on only one model, use it.
        2) If a field exists on both models:
            a) If a merge strategy is explicitly specified, use it.
            b) Choose the more recent value.

        For M2M Relationships:
        1) TODO: If a merge strategy is explicitly specified, use it.
        2) Take the union of both sets
        """
        #
        with transaction.atomic():
            merged_document = self.create_merged_document(records)

            # Order the records by date_modified so that as we traverse them
            # we can take the newer value when no merging strategy is specified
            ordering = merge_strategy.get('ordering', 'date_modified')
            records = records.order_by(ordering)
            generic_relation_field_names = set()
            foreign_key_relation_field_names = set()

            for field in model_fields:
                field_name = field.name
                if isinstance(field, GenericRelation):
                    generic_relation_field_names.add(field_name)
                    continue
                elif  field.one_to_many:
                    if field.related_name:
                        foreign_key_relation_field_names.add(field.related_name)
                    else:
                        foreign_key_relation_field_names.add('{}_set'.format(field_name))
                    continue
                if field.auto_created or field.many_to_many or field.one_to_one:
                    continue

                merge_method = merge_strategy.get(field_name, None)
                if callable(merge_method):
                    setattr(merged_document, field_name, merge_method(records))
                else:
                    for record in records:
                        current_value = getattr(merged_document, field_name)
                        record_value = getattr(record, field_name)

                        # Attribute is not yet set on the merged document so just use this value
                        if record_value and current_value and merge_method:
                            # If a merge strategy is explicitly specified we'll use it.
                            # Otherwise take the more recently modified value
                            merge_func = getattr(self, merge_method)
                            merged_value = merge_func(record_value, current_value)
                        else:
                            merged_value = record_value

                        if merged_value:
                            setattr(merged_document, field_name, merged_value)

            merged_document.save()

            # Update ALL foreign key relations to reference merged document
            for record in records:
                for field_name in foreign_key_relation_field_names:
                    merged_fk_relation = getattr(merged_document, field_name)
                    fk_related_record_manager = getattr(record, field_name)
                    for item in fk_related_record_manager.all():
                        try:
                            with transaction.atomic():
                                merged_fk_relation.add(item)
                        except IntegrityError:
                            pass

            # Update the generic relations
            for record in records:
                for field_name in generic_relation_field_names:
                    generic_relation = getattr(record, field_name)
                    for item in generic_relation.all():
                        item.object_id = merged_document.id
                        item.save()

            # Take the union of any M2M relationships
            for record in records:
                for field in model_fields:
                    if field.many_to_many:
                        field_name = field.name
                        related_record_manager = getattr(record, field_name)
                        model_manager = related_record_manager.through.objects

                        merge_method_name = 'merge_{}'.format(field_name)
                        if hasattr(self, merge_method_name):
                            # If a merge method for this field exists, use it
                            merge_method = getattr(self, merge_method_name)
                            merge_method(record, merged_document)
                        elif model_manager and hasattr(model_manager, 'merge_records'):
                            merge_method = getattr(model_manager, 'merge_records')
                            merge_method(record, merged_document)
                        else:
                            merged_related_records = getattr(merged_document, field_name)
                            related_records = related_record_manager.all()
                            merged_related_records.add(*related_records)
                # Delete the merged source record
                record.delete()


            return self.post_process_merged_document(merged_document)
