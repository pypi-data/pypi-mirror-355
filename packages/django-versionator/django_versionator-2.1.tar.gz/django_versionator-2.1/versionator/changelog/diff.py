from django.db.models import ForeignKey, ManyToManyField
from django.utils.functional import cached_property
from django.utils.html import escape

from data_fetcher import PrimaryKeyFetcherFactory
from data_fetcher.core import LazyFetchedValue

from versionator.changelog.diff_utils import list_diff, text_compare_inline
from versionator.core import M2MTextField


class DiffObject:

    action = "edited"

    def __init__(self, current_version, previous_version, field_obj):
        self.current_version = current_version
        self.previous_version = previous_version
        self.field = field_obj


class CachedComputationDiff(DiffObject):
    def compute_diffs(self):
        """
        should return a 3-tuple: (joint, before, after)
        """
        raise NotImplementedError()

    @cached_property
    def _diffs(self):
        return self.compute_diffs()

    def get_combined_diff(self):
        return self._diffs[0]

    def get_before_diff(self):
        return self._diffs[1]

    def get_after_diff(self):
        return self._diffs[2]


class ScalarDiffObject(CachedComputationDiff):
    def compute_diffs(self):
        prev_db_value = self.previous_version.serializable_value(
            self.field.name
        )
        current_db_value = self.current_version.serializable_value(
            self.field.name
        )

        if self.field.choices:
            # if a field is a choice field e.g. chars or ints used to represent a list of choices,
            # then its value is just that database, non-bilingual char/int value
            # fortunately model instances provide a hook to get the displayed, translated value
            choices_by_attr_value = dict(self.field.choices)
            if not choices_by_attr_value.get(None, None):
                choices_by_attr_value[None] = "empty"
            previous_value = choices_by_attr_value.get(
                prev_db_value, prev_db_value
            )
            current_value = choices_by_attr_value.get(
                current_db_value, current_db_value
            )

        else:  # just use the normal attribute
            previous_value = prev_db_value
            current_value = current_db_value

        joint, before, after = text_compare_inline(
            get_str_val(previous_value),
            get_str_val(current_value),
        )

        return (joint, before, after)


class CreateDiff:

    action = "created"

    def __init__(self):
        self.field = None

    def _get_created_str(self):
        return "created"

    def get_before_diff(self):
        return ""

    def get_after_diff(self):
        return self._get_created_str()

    def get_combined_diff(self):
        return self._get_created_str()


class DeleteDiff:

    action = "deleted"

    def __init__(self):
        self.field = None

    def _get_deleted_str(self):
        return "deleted"

    def get_before_diff(self):
        return ""

    def get_after_diff(self):
        return self._get_deleted_str()

    def get_combined_diff(self):
        return self._get_deleted_str()


class M2MDiffObject(CachedComputationDiff):
    def compute_diffs(self):
        prev_instances = self.previous_instances().get()
        current_instances = self.current_instances().get()

        def get_name(inst):
            return inst.__str__()

        before_list = sorted([*prev_instances], key=get_name)
        after_list = sorted([*current_instances], key=get_name)

        joint, before, after = list_diff(before_list, after_list)

        return (joint, before, after)

    def previous_instances(self):
        return self.get_lazy_related_records(
            self.previous_version.get_m2m_ids(self.field.name)
        )

    def current_instances(self):
        return self.get_lazy_related_records(
            self.current_version.get_m2m_ids(self.field.name)
        )

    def get_lazy_related_records(self, ids):
        related_model = self.field.related_model
        related_fetcher = PrimaryKeyFetcherFactory.get_model_by_id_fetcher(
            related_model
        ).get_instance()
        return related_fetcher.get_many_lazy(ids)

    def queue_dependencies(self):
        self.previous_instances()
        self.current_instances()


class ForeignKeyDiffObject(CachedComputationDiff):
    def compute_diffs(self):
        previous_instance = self.get_before_record().get()
        current_instance = self.get_after_record().get()

        joint, before, after = text_compare_inline(
            get_str_val(previous_instance),
            get_str_val(current_instance),
        )

        return joint, before, after

    def get_record_lazy(self, id):
        if not id:
            return LazyFetchedValue(lambda: None)

        related_model = self.field.remote_field.model
        related_fetcher_cls = (
            PrimaryKeyFetcherFactory.get_model_by_id_fetcher(related_model)
        ).get_instance()
        return related_fetcher_cls.get_lazy(id)

    def get_before_record(self):
        return self.get_record_lazy(
            self.previous_version.serializable_value(self.field.name)
        )

    def get_after_record(self):
        return self.get_record_lazy(
            self.current_version.serializable_value(self.field.name)
        )

    def queue_dependencies(self):
        self.get_before_record()
        self.get_after_record()


def is_field_different_accross_versions(
    current_version, previous_version, field_name
):

    current_db_value = current_version.serializable_value(field_name)
    prev_db_value = previous_version.serializable_value(field_name)

    field_obj = current_version._meta.get_field(field_name)
    if isinstance(field_obj, M2MTextField):
        return current_db_value != prev_db_value

    if current_db_value == prev_db_value or (
        # consider "" vs. None to be non-diff worthy
        {current_db_value, prev_db_value}.issubset({None, ""})
    ):
        return False
    return True


def get_field_diff_for_version_pair(
    current_version, previous_version, field, config
):
    if not is_field_different_accross_versions(
        current_version, previous_version, field.name
    ):
        return None

    DiffClass = config.get_diff_class(field)

    diff_obj = DiffClass(current_version, previous_version, field)
    return diff_obj


def get_str_val(fetched_field_value):
    if isinstance(fetched_field_value, str):
        return escape(fetched_field_value)
    elif fetched_field_value in (None, ""):
        return "empty"
    if isinstance(fetched_field_value, object):
        return escape(fetched_field_value.__str__())
