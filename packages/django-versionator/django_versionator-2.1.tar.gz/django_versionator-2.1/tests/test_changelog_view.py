from django.urls import reverse

from data_fetcher.global_request_context import GlobalRequest

from sample_app.data_factories import BookFactory


def test_sample_app_view(client):

    BookFactory.create_batch(100)
    for b in BookFactory.create_batch(50):
        b.reset_version_attrs()
        b.title = "new title"
        b.save()

    url = reverse("changelog")
    response = client.get(url)
    assert response.status_code == 200

    assert len(response.context["entries"]) == 50


def test_sample_view_with_abstract_class(
    client, django_assert_max_num_queries, django_assert_num_queries
):
    BookFactory.create_batch(100)
    for b in BookFactory.create_batch(50):
        b.reset_version_attrs()
        b.title = "new title"
        b.save()

    url = reverse("changelog_cls")
    with django_assert_num_queries(104):
        # number doesn't matter
        # just checking that it's high enough to be sure it's not batched
        response = client.get(url)

    assert len(response.context["entries"]) == 50

    # with data-fetchers, the view should be using batching
    with GlobalRequest(), django_assert_max_num_queries(10):
        response = client.get(url)
    assert response.status_code == 200

    assert len(response.context["entries"]) == 50
