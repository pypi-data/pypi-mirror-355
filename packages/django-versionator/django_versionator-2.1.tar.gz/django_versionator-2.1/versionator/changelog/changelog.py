from dataclasses import dataclass
from functools import lru_cache
from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Model
from django.utils.functional import cached_property

from data_fetcher import PrimaryKeyFetcherFactory
from data_fetcher.core import LazyFetchedValue

from versionator.changelog.util import get_diffable_fields_for_model
from versionator.core import VersionModel

from .diff import (
    CreateDiff,
    DeleteDiff,
    ForeignKeyDiffObject,
    M2MDiffObject,
    ScalarDiffObject,
    get_field_diff_for_version_pair,
)

EXCLUDE_CREATES = "exlude_creates"
INCLUDE_CREATES = "include_creates"
ONLY_CREATES = "only_creates"

CREATE_MODES = [EXCLUDE_CREATES, INCLUDE_CREATES, ONLY_CREATES]


class ChangelogConfig:
    INCLUDE_CREATES = INCLUDE_CREATES
    EXCLUDE_CREATES = EXCLUDE_CREATES
    ONLY_CREATES = ONLY_CREATES

    models = None
    page_size = 50
    start_date = None
    end_date = None
    create_mode = INCLUDE_CREATES
    fields_by_model = None

    def __init__(
        self,
        models=None,
        start_date=None,
        end_date=None,
        page_size=None,
        fields_by_model=None,
        create_mode=None,
    ):
        if models:
            self.models = models
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if page_size:
            self.page_size = page_size

        if fields_by_model:
            self.fields_by_model = fields_by_model

        if create_mode:
            assert create_mode in CREATE_MODES
            self.create_mode = create_mode

    def get_models(self) -> List[type]:
        if self.models:
            return self.models

        raise NotImplementedError(
            "You must implement get_models or define a models iterable"
        )

    def get_fields(self):
        if not hasattr(self, "fields"):
            return None

    def get_page_size(self) -> int:
        return self.page_size

    def get_user_ids(self):
        if not hasattr(self, "user_ids"):
            return None

    def get_create_mode(self) -> str:
        return self.create_mode

    def get_base_version_queryset_for_single_model(self, live_model):
        """
        Override to filter the version queryset for a single model
        good for single-record changelogs, filtering by user, etc.
        """
        history_model = live_model._history_class
        return history_model.objects.all()

    def get_fetcher_class(self) -> type:
        from versionator.changelog.consecutive_versions_retriever import (
            ConsecutiveVersionRetriever,
        )

        return ConsecutiveVersionRetriever

    def get_start_date(self):
        return self.start_date

    def get_end_date(self):
        return self.end_date

    def get_fields_by_model(self):
        """
        override this as a dict of model -> fields
        entries will be filtered in only
        if they have different values for these fields
        """
        return self.fields_by_model

    def get_diffable_fields_for_model(self, model):
        """
        Override this to filter out specific fields from being diffed
        This is different than get_fields_by_model
        it won't filter entries, only which fields diffs are shown
        """

        return get_diffable_fields_for_model(model)

    def get_livename_loader(self, model):
        if hasattr(model, "changelog_live_name_fetcher_class"):
            return model.changelog_live_name_fetcher_class.get_instance()

    def get_livename(self, live_record):
        fetcher = self.get_livename_loader(live_record.__class__)
        if fetcher:
            return fetcher.get_lazy(live_record.id)

        if hasattr(live_record, "name"):
            return live_record.name

        return live_record.__str__()

    def get_diff_class(self, field):

        if hasattr(field, "get_changelog_diff_class"):
            return field.get_changelog_diff_class()

        if isinstance(field, models.ManyToManyField):
            return M2MDiffObject
        elif isinstance(field, models.ForeignKey):
            return ForeignKeyDiffObject
        else:
            return ScalarDiffObject


class SingleRecordChangelogConfig(ChangelogConfig):
    def __init__(self, record=None, **kwargs):
        assert (
            record is not None
        ), "must pass record kwarg to SingleRecordChangelogConfig"
        self.record = record
        super().__init__(**kwargs)

    def get_models(self):
        return [self.record.__class__]

    def get_base_version_queryset_for_single_model(self, live_model):
        return live_model._history_class.objects.filter(eternal=self.record)


class ChangelogEntry:
    def __init__(
        self,
        left_version: VersionModel,
        right_version: VersionModel,
        eternal: Model,
        config: ChangelogConfig,
    ):
        self.left_version = left_version
        self.right_version = right_version
        self.eternal = eternal
        self.config = config

    def _get_diffs(self) -> List:

        if self.left_version is None and self.right_version is not None:
            return [CreateDiff()]

        if self.left_version is not None and self.right_version is None:
            return [DeleteDiff()]

        specified_fields = self.config.get_fields()
        diffable_fields = self.config.get_diffable_fields_for_model(
            self.eternal.__class__
        )
        fields_to_diff = diffable_fields
        if specified_fields:
            fields_to_diff = [
                field for field in diffable_fields if field in specified_fields
            ]

        diffs = []
        for field in fields_to_diff:
            diff_obj = get_field_diff_for_version_pair(
                self.right_version,
                self.left_version,
                field=field,
                config=self.config,
            )
            if diff_obj is not None:

                if hasattr(diff_obj, "queue_dependencies"):
                    diff_obj.queue_dependencies()
                diffs.append(diff_obj)

        return diffs

    @cached_property
    def diffs(self):
        return self._get_diffs()

    def queue_deps(self):
        self._get_author_lazy()
        self._get_live_name_possibly_lazy()
        self.diffs

    def _get_live_name_possibly_lazy(self):
        livename = self.config.get_livename(self.eternal)

        return livename

    @cached_property
    def live_name(self):
        value = self._get_live_name_possibly_lazy()

        if isinstance(value, LazyFetchedValue):
            return value.get_val()

        return value

    def _get_author_lazy(self):
        if self.right_version and getattr(
            self.right_version, "edited_by_id", None
        ):
            fetcher = PrimaryKeyFetcherFactory.get_model_by_id_fetcher(
                get_user_model()
            ).get_instance()

            return fetcher.get_lazy(self.right_version.edited_by_id)

    @cached_property
    def author(self):
        author_lazy = self._get_author_lazy()
        if author_lazy:
            return author_lazy.get_val()


class Changelog:
    def __init__(self, config: ChangelogConfig):
        self.config = config

    @cached_property
    def _fetcher(self):
        FetcherCls = self.config.get_fetcher_class()
        fetcher = FetcherCls(
            config=self.config,
        )
        return fetcher

    def get_entries(self, page_num, prefetch_deps=True):
        entries = self._fetcher.get_entries(page_num, prefetch_deps)
        if prefetch_deps:
            for e in entries:
                e.queue_deps()

        return entries

    def get_page_count(self):
        return self._fetcher.get_page_count()

    def get_entry_count(self) -> int:
        return self._fetcher.get_entry_count()
