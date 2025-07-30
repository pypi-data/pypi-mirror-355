# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 Northwestern University.
#
# invenio-sitemap is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import xmlschema

from invenio_sitemap.tasks import (
    _get_latest_lastmod,
    _iterate_url_entries,
    update_sitemap_cache,
)

from .fake_sitemap_sections import FakeSitemapSection1


def test_url_entries_generation(app):
    entries_expected = [
        {
            "loc": "https://127.0.0.1:5000/foo",
            "lastmod": "2025-02-02T00:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/bar",
            "lastmod": "2025-02-02T06:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/baz",
            "lastmod": "2025-02-01T00:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/barun",
            "lastmod": "2025-01-01T00:00:00Z",
        },
    ]

    entries_generated = list(_iterate_url_entries())

    assert entries_expected == entries_generated


def test_latest_lastmod():
    entries = [
        {
            "loc": "https://127.0.0.1:5000/foo",
            "lastmod": "2025-02-02T00:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/bar",
            "lastmod": "2025-02-02T06:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/baz",
            "lastmod": "2025-02-01T00:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/barun",
            "lastmod": "2025-01-01T00:00:00Z",
        },
    ]

    lastmod = _get_latest_lastmod(entries)

    assert "2025-02-02T06:00:00Z" == lastmod


# Integration


def test_sitemap_404(client, empty_cache):
    resp = client.get("/sitemap_0.xml")

    assert 404 == resp.status_code


def test_sitemap_has_valid_structure(client, primed_cache):
    schema = xmlschema.XMLSchema("tests/xsds/sitemap.xsd")

    resp = client.get("/sitemap_0.xml")

    assert 200 == resp.status_code
    assert "application/xml" == resp.content_type
    schema.validate(resp.data)


def test_sitemap_content(client, primed_cache):
    expected_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<urlset\n"
        '  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        '  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n'
        "  <url>\n"
        "    <loc>https://127.0.0.1:5000/baz</loc>\n"
        "    <lastmod>2025-02-01T00:00:00Z</lastmod>\n"
        "  </url>\n"
        "  <url>\n"
        "    <loc>https://127.0.0.1:5000/barun</loc>\n"
        "    <lastmod>2025-01-01T00:00:00Z</lastmod>\n"
        "  </url>\n"
        "</urlset>"
    )

    resp = client.get("/sitemap_1.xml")

    assert expected_content == resp.text


def test_urls_eliminated_between_cache_refresh(
    client, primed_cache, set_app_config_fn_scoped
):
    resp = client.get("/sitemap_1.xml")
    assert 200 == resp.status_code
    set_app_config_fn_scoped(
        {
            "SITEMAP_MAX_ENTRY_COUNT": 3,
            "SITEMAP_SECTIONS": [
                FakeSitemapSection1(),
            ],
        }
    )
    update_sitemap_cache()

    resp = client.get("/sitemap_1.xml")

    assert 404 == resp.status_code
