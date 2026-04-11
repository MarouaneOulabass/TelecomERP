# -*- coding: utf-8 -*-
"""Pre-migration: rename adresse -> address on telecom_site."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("telecom_site: renaming column adresse -> address on telecom_site")
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_site
        RENAME COLUMN adresse TO address
    """)
