# -*- coding: utf-8 -*-
"""Pre-migration: rename montant -> amount on telecom_cost_entry."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("telecom_cost: renaming column montant -> amount on telecom_cost_entry")
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_cost_entry
        RENAME COLUMN montant TO amount
    """)
