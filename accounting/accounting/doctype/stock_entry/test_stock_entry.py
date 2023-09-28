# Copyright (c) 2023, Akhil and Contributors
# See license.txt

from typing import Literal

import frappe
from accounting.utils import generate_random_string, get_random_integer
from frappe.tests.utils import FrappeTestCase


def create_entry(
    entry_type: Literal["Receipt", "Consume", "Transfer"],
    items: list,
    source_warehouse: str | None = None,
    target_warehouse: str | None = None,
):
    data = {
        "doctype": "Stock Entry",
        "entry_type": entry_type,
        "items": items,
    }

    # Add source warehouse if present
    if source_warehouse:
        data["source_warehouse"] = source_warehouse

    # Add target warehouse if present
    if target_warehouse:
        data["target_warehouse"] = target_warehouse

    return frappe.get_doc(data).insert()


class TestStockEntry(FrappeTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incoming_warehouse_name = generate_random_string()
        self.outgoing_warehouse_name = generate_random_string()
        self.main_warehouse_name = generate_random_string()

    def setUp(self):
        frappe.set_user("Administrator")

        # Create some items
        name = generate_random_string()
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_name": name,
            }
        ).insert()
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_name": name[::-1],
            }
        ).insert()

        # Create some warehouses
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.incoming_warehouse_name,
                "address": generate_random_string(),
            }
        ).insert()
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.outgoing_warehouse_name,
                "address": generate_random_string(),
            }
        ).insert()
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.main_warehouse_name,
                "address": generate_random_string(),
            }
        )

    def tearDown(self):
        frappe.db.rollback()

    def test_create_stock_entry_without_mandatory_fields(self):
        frappe.set_user("Administrator")
        doc = frappe.get_doc(
            {
                "doctype": "Stock Entry",
            }
        )
        with self.assertRaises(frappe.exceptions.ValidationError):
            doc.insert()

    def test_create_stock_entry(self):
        frappe.set_user("Administrator")
        item_names = frappe.db.get_all("Item", fields=["name"])

        items = []
        for item in item_names:
            items.append(
                {
                    "item": item["name"],
                    "quantity": get_random_integer(minimum=10),
                    "rate": get_random_integer(100, 1000),
                }
            )

        # Test receiving items
        doc = create_entry("Receipt", items, None, self.incoming_warehouse_name)
        created_stock_entry = frappe.get_doc("Stock Entry", doc.name)
        self.assertEqual(created_stock_entry.entry_type, "Receipt")

        # Check ledger entries
        for item in items:
            data = frappe.db.get(
                "Stock Ledger Entry",
                {
                    "item": item["item"],
                    "warehouse": self.incoming_warehouse_name,
                },
            )
            self.assertEqual(item["quantity"], data.quantity)
            self.assertEqual(item["rate"], data.rate)

        for i, item in enumerate(items):
            items[i] = {
                "item": item["item"],
                "quantity": get_random_integer(maximum=item["quantity"]),
                "rate": item["rate"],
            }
        doc = create_entry(
            "Transfer",
            items,
            self.incoming_warehouse_name,
            self.outgoing_warehouse_name,
        )
        created_stock_entry = frappe.get_doc("Stock Entry", doc.name)
        self.assertEqual(created_stock_entry.entry_type, "Transfer")

        for i, item in enumerate(items):
            items[i] = {
                "item": item["item"],
                "quantity": get_random_integer(maximum=item["quantity"]),
                "rate": get_random_integer(100, 1000),
            }
        doc = create_entry("Consume", items, self.outgoing_warehouse_name, None)
        created_stock_entry = frappe.get_doc("Stock Entry", doc.name)
        self.assertEqual(created_stock_entry.entry_type, "Consume")

    def test_create_guest(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.exceptions.PermissionError):
            create_entry(entry_type="Receipt", items=[])

    def test_read_guest(self):
        frappe.set_user("Guest")
        self.assertFalse(frappe.has_permission("Stock Entry"))
