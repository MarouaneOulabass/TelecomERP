# -*- coding: utf-8 -*-
"""Pre-migration: rename montant -> amount on telecom_caution_bancaire."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info("telecom_contract: renaming column montant -> amount on telecom_caution_bancaire")
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_caution_bancaire
        RENAME COLUMN montant TO amount
    """)
