import operator
from collections import defaultdict
from functools import reduce

from django.core.paginator import Paginator
from django.db.models import CharField, F, OuterRef, Q, Subquery, Value
from django.utils.functional import cached_property

from versionator.changelog.changelog import (
    EXCLUDE_CREATES,
    ONLY_CREATES,
    ChangelogEntry,
)
from versionator.changelog.util import get_diffable_fields_for_model

neverQ = Q(pk=None)
anyQ = ~neverQ


from .util import get_diffable_fields_for_model


def get_all_versions_for_live_model(self, live_model):
    """
    You can override this to allow for custom extra filtering
    """
    history_model = live_model._history_class
    return history_model.objects.all()


class ConsecutiveVersionRetriever:
    def __init__(
        self,
        config=None,
        get_versions_for_live_model: callable = None,
    ):

        if (
            config.get_fields_by_model()
            and config.get_create_mode() == "ONLY_CREATES"
        ):
            raise Exception(
                "cant only show creations while excluding them or comparing specific fields"
            )

        self.config = config

        if not get_versions_for_live_model:
            self.get_versions_for_live_model = get_versions_for_live_model

    @staticmethod
    def unionize_querysets(qs1, qs2):
        return qs1.union(qs2)

    def _get_values_qs_for_single_model(self, live_model):
        history_model = live_model._history_class

        base_qs = self.config.get_base_version_queryset_for_single_model(
            live_model
        )

        qs = base_qs.with_previous_version_id()

        create_mode = self.config.get_create_mode()
        if create_mode == EXCLUDE_CREATES:
            qs = qs.filter(previous_version_id__isnull=False)

        elif create_mode == ONLY_CREATES:
            qs = qs.filter(previous_version_id__isnull=True)

        start_date = self.config.get_start_date()
        end_date = self.config.get_end_date()

        if start_date:
            qs = qs.filter(timestamp__gte=start_date)

        if end_date:
            qs = qs.filter(timestamp__lte=end_date)

        fields_by_model = self.config.get_fields_by_model()

        if fields_by_model and fields_by_model.get(live_model, None):
            field_names = fields_by_model[live_model]
            # also filter out creations when comparing specific fields
            qs = qs.filter(previous_version_id__isnull=False)

            field_objs = [
                f
                for f in get_diffable_fields_for_model(live_model)
                if f.name in field_names
            ]

            get_annotation_name = lambda field: f"_previous_{field.name}"
            for f in field_objs:
                prev_field_value_subquery = Subquery(
                    history_model.objects.filter(
                        id=OuterRef("previous_version_id")
                    ).values(f.attname)[:1]
                )

                qs = qs.annotate(
                    **{get_annotation_name(f): prev_field_value_subquery}
                )

            # once annotated, we can filter on any OR differences
            # the difference doesn't seem to check for nulls vs. values, so we check that manually
            field_difference_filters = [
                (
                    ~Q(**{get_annotation_name(field): F(field.attname)})
                    | (
                        Q(**{f"{get_annotation_name(field)}__isnull": False})
                        & Q(**{f"{field.attname}__isnull": True})
                    )
                    | (
                        Q(**{f"{get_annotation_name(field)}__isnull": True})
                        & Q(**{f"{field.attname}__isnull": False})
                    )
                )
                for field in field_objs
            ]
            combined_filter = reduce(
                operator.__or__, field_difference_filters, neverQ
            )

            qs = qs.filter(combined_filter)

        qs = (
            qs.annotate(model_name=Value(live_model.__name__, CharField()))
            .only(
                "timestamp",
                "id",
                "eternal_id",
                "model_name",
                "previous_version_id",
            )
            .order_by("-timestamp")
            .values(
                "timestamp",
                "id",
                "eternal_id",
                "model_name",
                "previous_version_id",
            )
        )

        return qs

    @cached_property
    def _paginator(self):
        fields_by_model = self.config.get_fields_by_model()
        if fields_by_model is not None:
            history_querysets = [
                self._get_values_qs_for_single_model(m)
                for m in fields_by_model.keys()
            ]
        else:
            history_querysets = [
                self._get_values_qs_for_single_model(m)
                for m in self.config.get_models()
            ]

        qs_values_union = reduce(self.unionize_querysets, history_querysets)
        sorted_union = qs_values_union.order_by("-timestamp")
        paginated_qs = Paginator(sorted_union, self.config.get_page_size())
        return paginated_qs

    def get_entries(self, page_num, prefetch_deps=False):
        versions = self._paginator.page(page_num).object_list
        entries = self._get_fully_fetched_entries(versions)
        # if prefetch_deps:
        #     self._prefetch_entry_dependencies(entries)

        return entries

    def get_entry_count(self):
        return self._paginator.count

    def get_page_count(self):
        return self._paginator.num_pages

    def _get_fully_fetched_entries(self, slim_versions):
        """
        our paginated qs only hold 'slim' dict records:
        { id, previous_version_id, eternal_id, model_name}

        we need to fetch the entire left/right/eternal records
        """
        models_by_name = {m.__name__: m for m in self.config.get_models()}

        eternal_ids_to_fetch_by_model = defaultdict(list)
        version_ids_to_fetch_by_model = defaultdict(list)

        for slim_ver in slim_versions:
            eternal_model = models_by_name[slim_ver["model_name"]]
            hist_model = eternal_model._history_class
            eternal_ids_to_fetch_by_model[eternal_model].append(
                slim_ver["eternal_id"]
            )
            version_ids_to_fetch_by_model[hist_model].append(slim_ver["id"])
            if slim_ver.get("previous_version_id", None):
                version_ids_to_fetch_by_model[hist_model].append(
                    slim_ver["previous_version_id"]
                )

        eternal_records_by_pair_id = {}
        version_records_by_pair_id = {}

        for model, ids in eternal_ids_to_fetch_by_model.items():
            for record in model.objects.filter(id__in=ids):
                eternal_records_by_pair_id[(model, record.id)] = record

        for model, ids in version_ids_to_fetch_by_model.items():
            for record in model.objects.filter(id__in=ids):
                version_records_by_pair_id[(model, record.id)] = record

        resolved_list = []
        for slim_ver in slim_versions:
            eternal_model = models_by_name[slim_ver["model_name"]]
            hist_model = eternal_model._history_class
            resolved = {}

            resolved["eternal"] = eternal_records_by_pair_id[
                (eternal_model, slim_ver["eternal_id"])
            ]

            resolved["version"] = version_records_by_pair_id[
                (hist_model, slim_ver["id"])
            ]

            if slim_ver.get("previous_version_id", None):
                resolved["previous_version"] = version_records_by_pair_id[
                    (hist_model, slim_ver["previous_version_id"])
                ]
            else:
                resolved["previous_version"] = None

            resolved_list.append(
                ChangelogEntry(
                    left_version=resolved["previous_version"],
                    right_version=resolved["version"],
                    eternal=resolved["eternal"],
                    config=self.config,
                )
            )

        return resolved_list
