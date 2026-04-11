# -*- coding: utf-8 -*-
"""Pre-migration: rename montant -> amount, montant_interets -> interest_amount
on telecom_cout_financier."""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info(
        "telecom_financing: renaming columns on telecom_cout_financier: "
        "montant -> amount, montant_interets -> interest_amount"
    )
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_cout_financier
        RENAME COLUMN montant TO amount
    """)
    # SQL direct : column rename during schema migration (ORM not available in pre-migration)
    cr.execute("""
        ALTER TABLE telecom_cout_financier
        RENAME COLUMN montant_interets TO interest_amount
    """)
