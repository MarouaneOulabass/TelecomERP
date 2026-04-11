#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo data generator — telecom.cost.entry
==========================================
Creates 50 cost entries across existing projects with a realistic
distribution of categories, amounts, and states.

Run:
    docker compose exec -T odoo python3 /mnt/extra-addons/demo_cost_data.py

Prerequisites:
    - Odoo is running with TelecomERP modules installed
    - At least 1 project with lots exists in the database
    - telecom_cost module is installed (cost types pre-loaded)
"""
import random
import sys
import os
from datetime import date, timedelta

# -- Odoo bootstrap ----------------------------------------------------------
try:
    import odoo
    from odoo import api, SUPERUSER_ID
except ImportError:
    sys.exit("ERROR: Odoo is not available. Run inside the Odoo container.")

config_path = os.environ.get('ODOO_RC', '/etc/odoo/odoo.conf')
odoo.tools.config.parse_config(['--config', config_path])

db_name = odoo.tools.config.get('db_name', 'telecomerp')
registry = odoo.registry(db_name)

# -- Constants ----------------------------------------------------------------
NUM_ENTRIES = 50
MIN_AMOUNT = 5000
MAX_AMOUNT = 100000
# Weight distribution: some categories appear more often
CATEGORY_WEIGHTS = {
    'main_oeuvre': 30,
    'materiel': 25,
    'sous_traitance': 20,
    'carburant': 15,
    'location': 5,
    'frais_generaux': 3,
    'financier': 2,
}

DESCRIPTIONS = {
    'main_oeuvre': [
        'Equipe soudure fibre',
        'Techniciens installation BTS',
        'Main d\'oeuvre tirage cable',
        'Equipe genie civil',
        'Techniciens mesures RF',
    ],
    'materiel': [
        'Cable fibre optique 48FO',
        'Connecteurs SC/APC',
        'Boitiers d\'epissurage',
        'Equipements BTS Nokia',
        'Armoire electrique',
    ],
    'sous_traitance': [
        'Sous-traitance genie civil',
        'Prestation soudure FO',
        'Travaux courant fort',
        'Installation shelter',
        'Montage pylone',
    ],
    'carburant': [
        'Plein vehicule chantier',
        'Deplacement equipe terrain Casablanca',
        'Carburant nacelle',
        'Frais peage autoroute',
        'Deplacement equipe Rabat-Meknes',
    ],
    'location': [
        'Location nacelle 20m',
        'Location groupe electrogene',
        'Location trancheuse',
        'Location vehicule utilitaire',
    ],
    'frais_generaux': [
        'Assurance chantier',
        'Frais gardiennage site',
        'Fournitures bureau chantier',
    ],
    'financier': [
        'Caution bancaire provisoire',
        'Interets credit chantier',
    ],
}

STATES = ['confirmed', 'validated']
STATE_WEIGHTS = [40, 60]  # 40% confirmed, 60% validated


def weighted_choice(choices_weights):
    """Return a key from a dict {choice: weight}."""
    items = list(choices_weights.keys())
    weights = list(choices_weights.values())
    return random.choices(items, weights=weights, k=1)[0]


def main():
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # -- Fetch existing projects with lots --------------------------------
        projects = env['project.project'].search([], limit=10)
        if not projects:
            print("ERROR: No projects found. Create projects first.")
            cr.rollback()
            return

        project_lots = {}
        for project in projects:
            lots = env['telecom.lot'].search([
                ('project_id', '=', project.id),
            ])
            if lots:
                project_lots[project] = lots

        if not project_lots:
            print("ERROR: No projects with lots found. Create lots first.")
            cr.rollback()
            return

        print(f"Found {len(project_lots)} project(s) with lots.")

        # -- Fetch cost types by category -------------------------------------
        cost_types_by_cat = {}
        all_types = env['telecom.cost.type'].search([])
        for ct in all_types:
            cost_types_by_cat.setdefault(ct.category, []).append(ct)

        if not all_types:
            print("ERROR: No cost types found. Install telecom_cost first.")
            cr.rollback()
            return

        print(f"Found {len(all_types)} cost type(s).")

        # -- Fetch tasks (optional) -------------------------------------------
        all_tasks = env['project.task'].search([], limit=50)
        tasks_by_project = {}
        for task in all_tasks:
            tasks_by_project.setdefault(task.project_id.id, []).append(task)

        # -- Generate entries -------------------------------------------------
        created = 0
        for i in range(NUM_ENTRIES):
            # Pick project + lot
            project = random.choice(list(project_lots.keys()))
            lot = random.choice(project_lots[project])

            # Pick category and cost type
            category = weighted_choice(CATEGORY_WEIGHTS)
            types_for_cat = cost_types_by_cat.get(category)
            if not types_for_cat:
                # Fallback to any type
                cost_type = random.choice(all_types)
                category = cost_type.category
            else:
                cost_type = random.choice(types_for_cat)

            # Pick description
            desc_list = DESCRIPTIONS.get(category, ['Cout divers'])
            description = random.choice(desc_list)

            # Random amount
            amount = round(random.uniform(MIN_AMOUNT, MAX_AMOUNT), 2)

            # Random date in last 6 months
            days_ago = random.randint(0, 180)
            entry_date = date.today() - timedelta(days=days_ago)

            # Maybe link a task (60% chance if tasks exist for this project)
            task_id = False
            project_tasks = tasks_by_project.get(project.id, [])
            if project_tasks and random.random() < 0.6:
                task_id = random.choice(project_tasks).id

            # State
            state = random.choices(STATES, weights=STATE_WEIGHTS, k=1)[0]

            # Create entry
            vals = {
                'date': entry_date,
                'cost_type_id': cost_type.id,
                'description': description,
                'project_id': project.id,
                'lot_id': lot.id,
                'task_id': task_id,
                'montant': amount,
                'source': 'manual',
            }

            try:
                entry = env['telecom.cost.entry'].create(vals)
                # Advance state
                if state == 'confirmed':
                    entry.action_confirm()
                elif state == 'validated':
                    entry.action_confirm()
                    entry.action_validate()
                created += 1
            except Exception as exc:
                print(f"  WARNING: Entry {i+1} skipped: {exc}")

        cr.commit()
        print(f"\nDone! Created {created}/{NUM_ENTRIES} cost entries.")
        print("Distribution across projects:")
        for project in project_lots:
            count = env['telecom.cost.entry'].search_count([
                ('project_id', '=', project.id),
            ])
            print(f"  - {project.name}: {count} entries")


if __name__ == '__main__':
    main()
