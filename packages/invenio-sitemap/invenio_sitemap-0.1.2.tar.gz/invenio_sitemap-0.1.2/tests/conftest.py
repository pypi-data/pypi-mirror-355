# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
# Copyright (C) 2025 Northwestern University.
#
# invenio-sitemap is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""


import pytest
from invenio_app.factory import create_app as _create_app
from invenio_cache import current_cache

from invenio_sitemap.tasks import update_sitemap_cache

from .fake_sitemap_sections import FakeSitemapSection1, FakeSitemapSection2


@pytest.fixture(scope="module")
def app_config(app_config):
    """Application config override."""
    app_config["SITE_UI_URL"] = "https://127.0.0.1:5000"
    app_config["SITE_API_URL"] = "https://127.0.0.1:5000/api"
    app_config["SITEMAP_MAX_ENTRY_COUNT"] = 2
    app_config["SITEMAP_SECTIONS"] = [
        FakeSitemapSection1(),
        FakeSitemapSection2(),
    ]
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return _create_app


@pytest.fixture(scope="function")
def empty_cache(app):
    """Clean cache."""
    try:
        current_cache.clear()
        yield current_cache
    finally:
        current_cache.clear()


@pytest.fixture(scope="function")
def primed_cache(app):
    """Load cache."""
    try:
        current_cache.clear()
        update_sitemap_cache()
        yield current_cache
    finally:
        current_cache.clear()
