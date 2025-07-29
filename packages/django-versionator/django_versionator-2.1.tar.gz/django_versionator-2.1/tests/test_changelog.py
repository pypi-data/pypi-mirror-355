from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

import pytest
from data_fetcher.global_request_context import GlobalRequest
from pytest_django.asserts import assertInHTML

from sample_app.data_factories import BookFactory
from sample_app.fetchers import BookNameFetcher
from sample_app.models import Author, Book, Tag
from versionator.changelog import Changelog, ChangelogConfig

changelog_config = ChangelogConfig(
    models=[Author, Book],
    page_size=2,
)


def test_simple_case():
    author1 = Author.objects.create(first_name="john", last_name="smith")
    author2 = Author.objects.create(first_name="jane", last_name="smith")
    book1 = Book.objects.create(author=author1, title="john's diary")

    book1_v1 = book1.versions.last()

    # refresh a new copy of this record to avoid history-row re-use
    book1.reset_version_attrs()
    book1.title = "jane's diary"
    book1.author = author2
    book1.save()

    book1_v2 = book1.versions.last()

    cl = Changelog(changelog_config)
    edit_entries = cl.get_entries(1)
    assert len(edit_entries) == 2

    assert edit_entries[0].right_version == book1_v2
    diffs = edit_entries[0].diffs
    assert len(diffs) == 2
    diffs_by_fields = {diff.field.name: diff for diff in diffs}

    # field-diffs might come in any order
    assert set(diffs_by_fields.keys()) == {
        "title",
        "author",
    }
    # they have field objects as well
    assert diffs_by_fields["title"].field == Book._meta.get_field("title")

    assert edit_entries[1].right_version == book1_v1

    second_entry_diffs = edit_entries[1].diffs
    assert second_entry_diffs[0].action == "created"

    assert edit_entries[0].eternal == edit_entries[1].eternal == book1

    # test that the book's loader is used to load the live name
    assert edit_entries[0].live_name == "jane's diary (jane smith)"

    assert cl.get_page_count() == 2
    assert cl.get_entry_count() == 4


def test_m2m_entries():

    changelog_config = ChangelogConfig(
        models=[Book],
        page_size=100,
    )
    changelog = Changelog(changelog_config)

    t1 = Tag.objects.create(name="Tag1")
    t2 = Tag.objects.create(name="Tag2")
    t3 = Tag.objects.create(name="Tag3")

    book = Book.objects.create(
        author=Author.objects.create(first_name="john", last_name="smith"),
        title="john's diary",
    )
    book.tags.add(t1, t2)

    book_v1 = book.versions.last()
    book.reset_version_attrs()

    book.tags.add(t3)
    book.tags.remove(t1)
    book.save()

    book_v2 = book.versions.last()

    edit_entries = changelog.get_entries(1)
    assert len(edit_entries) == 2

    latest_entry = edit_entries[0]
    latest_entry_diffs = latest_entry.diffs

    assert latest_entry.right_version == book_v2
    assert len(latest_entry_diffs) == 1

    m2m_diff = latest_entry_diffs[0]
    assert m2m_diff.action == "edited"
    assert m2m_diff.field.name == "tags"
    # non-added/removed tag show up without class in both before/after

    assertInHTML("<p class=''>Tag2</p>", m2m_diff.get_before_diff())
    assertInHTML("<p class=''>Tag2</p>", m2m_diff.get_after_diff())

    assertInHTML("<p class='diff_sub'>Tag1</p>", m2m_diff.get_before_diff())
    assertInHTML("<p class='diff_add'>Tag3</p>", m2m_diff.get_after_diff())

    assertInHTML("<p class=''>Tag2</p>", m2m_diff.get_combined_diff())
    assertInHTML("<p class='diff_sub'>Tag1</p>", m2m_diff.get_combined_diff())
    assertInHTML("<p class='diff_add'>Tag3</p>", m2m_diff.get_combined_diff())


def test_num_queries_batched(django_assert_max_num_queries):
    books = BookFactory.create_batch(50)

    for b in books:
        b.reset_version_attrs()
        b.title = "new title"
        b.save()

    changelog_config = ChangelogConfig(
        models=[Book],
        page_size=100,
    )

    with django_assert_max_num_queries(0):
        # instantiating the changelog object should not make any queries
        cl = Changelog(changelog_config)

    batch_load_spy = Mock()

    real_batch_load = BookNameFetcher.batch_load

    def mocked_batch_load(*args, **kwargs):
        batch_load_spy(*args, **kwargs)
        return real_batch_load(*args, **kwargs)

    with (
        GlobalRequest(),
        patch(
            "sample_app.fetchers.BookNameFetcher.batch_load",
            staticmethod(mocked_batch_load),
        ),
        django_assert_max_num_queries(10),
    ):
        entries = cl.get_entries(1)
        for entry in entries:
            entry.live_name

    assert batch_load_spy.call_count == 1


def test_authors_are_batched(django_assert_max_num_queries):

    books = BookFactory.create_batch(100)
    for i, b in enumerate(books):
        b.reset_version_attrs()
        b.title = "new title"
        b.save()
        last_ver = b.versions.last()
        last_ver.edited_by = get_user_model().objects.create_user(f"test_{i}")
        last_ver.save()

    changelog_config = ChangelogConfig(
        models=[Book],
        page_size=100,
    )
    changelog = Changelog(changelog_config)

    with GlobalRequest(), django_assert_max_num_queries(10):
        entries = changelog.get_entries(1)
        for entry in entries:
            assert entry.author is not None
