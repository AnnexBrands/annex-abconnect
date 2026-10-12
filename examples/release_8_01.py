"""8_01 company packing, freight, add-on, and tracking examples.

Set AB_OPERATION and AB_PAYLOAD_FILE to an operation name and JSON arguments.
Mutation examples additionally require AB_RUN_MUTATIONS=1. Use staging first.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from ab import ABConnectAPI


def main():
    api = ABConnectAPI(env="staging")
    operation = os.environ["AB_OPERATION"]
    arguments = json.loads(Path(os.environ["AB_PAYLOAD_FILE"]).read_text())
    if operation == 'companies.get_inventory':
        return api.companies.get_inventory(**arguments)
    if operation == 'companies.create_inventory':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.create_inventory(**arguments)
    if operation == 'companies.update_inventory':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.update_inventory(**arguments)
    if operation == 'companies.delete_inventory':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.delete_inventory(**arguments)
    if operation == 'companies.get_materials':
        return api.companies.get_materials(**arguments)
    if operation == 'companies.get_default_pallet':
        return api.companies.get_default_pallet(**arguments)
    if operation == 'companies.get_stock_boxes':
        return api.companies.get_stock_boxes(**arguments)
    if operation == 'companies.get_d_containers':
        return api.companies.get_d_containers(**arguments)
    if operation == 'companies.pack_inventory':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.pack_inventory(**arguments)
    if operation == 'companies.pack_hierarchy':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.pack_hierarchy(**arguments)
    if operation == 'companies.pack_inventories':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.pack_inventories(**arguments)
    if operation == 'companies.get_handling_unit_materials':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.get_handling_unit_materials(**arguments)
    if operation == 'companies.validate_handling_unit':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.validate_handling_unit(**arguments)
    if operation == 'companies.pack_handling_units':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.companies.pack_handling_units(**arguments)
    if operation == 'jobs.freight_providers.create_final_override':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.freight_providers.create_final_override(**arguments)
    if operation == 'jobs.freight_providers.select_rate_quote':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.freight_providers.select_rate_quote(**arguments)
    if operation == 'jobs.freight_providers.save_final_quote':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.freight_providers.save_final_quote(**arguments)
    if operation == 'jobs.tracking.shipment_history':
        return api.jobs.tracking.shipment_history(**arguments)
    if operation == 'jobs.tracking.shipment_documents':
        return api.jobs.tracking.shipment_documents(**arguments)
    if operation == 'jobs.update_inventory_info':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.update_inventory_info(**arguments)
    if operation == 'jobs.add_ons.get_all':
        return api.jobs.add_ons.get_all(**arguments)
    if operation == 'jobs.add_ons.save':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.add_ons.save(**arguments)
    if operation == 'jobs.add_ons.delete':
        if os.environ.get("AB_RUN_MUTATIONS") != "1":
            raise ValueError("Set AB_RUN_MUTATIONS=1 for an authorized staging mutation")
        return api.jobs.add_ons.delete(**arguments)
    if operation == 'lookup.get_addons':
        return api.lookup.get_addons(**arguments)
    if operation == 'jobs.freight_providers.get_quotes':
        return api.jobs.freight_providers.get_quotes(**arguments)
    if operation == "jobs.payment.exchange":
        return api.jobs.payment.exchange(**arguments)
    if operation == "jobs.form.invoice_editable":
        return api.jobs.form.invoice_editable(**arguments)
    if operation == "jobs.form.usar_editable":
        return api.jobs.form.usar_editable(**arguments)
    if operation == "lookup.get_container_types":
        return api.lookup.get_container_types(**arguments)
    if operation == "lookup.get_cpacks":
        return api.lookup.get_cpacks(**arguments)
    if operation == "lookup.get_container_fills":
        return api.lookup.get_container_fills(**arguments)
    raise ValueError(f"Unknown AB_OPERATION: {operation}")


if __name__ == "__main__":
    main()
