# -*- coding: utf-8 -*-
"""Pre-migration: rename montant -> amount on telecom_plein_carburant."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("telecom_carburant: renaming column montant -> amount on telecom_plein_carburant")
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_plein_carburant
        RENAME COLUMN montant TO amount
    """)
