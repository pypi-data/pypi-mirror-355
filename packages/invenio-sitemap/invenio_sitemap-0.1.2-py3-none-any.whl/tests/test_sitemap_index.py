# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 Northwestern University.
#
# invenio-sitemap is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import xmlschema

from invenio_sitemap.tasks import _iterate_sitemap_entries
from invenio_sitemap.utils import iterate_urls_of_sitemap_indices


def test_sitemap_entries_generation(app):
    lastmods = [
        "2025-02-02T06:00:00Z",
        "2025-02-01T00:00:00Z",
    ]

    entries_generated = list(_iterate_sitemap_entries(lastmods))

    entries_expected = [
        {
            "loc": "https://127.0.0.1:5000/sitemap_0.xml",
            "lastmod": "2025-02-02T06:00:00Z",
        },
        {
            "loc": "https://127.0.0.1:5000/sitemap_1.xml",
            "lastmod": "2025-02-01T00:00:00Z",
        },
    ]
    assert entries_expected == entries_generated


def test_sitemap_index_has_valid_structure(client, primed_cache):
    schema = xmlschema.XMLSchema("tests/xsds/siteindex.xsd")

    resp = client.get("/sitemap_index_0.xml")

    assert 200 == resp.status_code
    schema.validate(resp.data)


def test_sitemap_index_content(client, primed_cache):
    expected_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <sitemap>\n"
        "    <loc>https://127.0.0.1:5000/sitemap_0.xml</loc>\n"
        "    <lastmod>2025-02-02T06:00:00Z</lastmod>\n"
        "  </sitemap>\n"
        "  <sitemap>\n"
        "    <loc>https://127.0.0.1:5000/sitemap_1.xml</loc>\n"
        "    <lastmod>2025-02-01T00:00:00Z</lastmod>\n"
        "  </sitemap>\n"
        "</sitemapindex>"
    )

    resp = client.get("/sitemap_index_0.xml")

    assert expected_content == resp.text


def test_iterate_urls_of_sitemap_indices(primed_cache):
    urls = list(iterate_urls_of_sitemap_indices())

    assert ["https://127.0.0.1:5000/sitemap_index_0.xml"] == urls
