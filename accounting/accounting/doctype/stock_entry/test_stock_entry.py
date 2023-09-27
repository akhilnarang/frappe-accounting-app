# Copyright (c) 2023, Akhil and Contributors
# See license.txt

import random
import string

import frappe
from frappe.tests.utils import FrappeTestCase


class TestStockEntry(FrappeTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incoming_warehouse_name = "".join(random.choices(string.ascii_letters, k=10))
        self.outgoing_warehouse_name = "".join(random.choices(string.ascii_letters, k=10))
        self.main_warehouse_name = "".join(random.choices(string.ascii_letters, k=10))

    def setUp(self):
        frappe.set_user("Administrator")

        # Create some items
        name = "".join(random.choices(string.ascii_letters, k=10))
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
                "address": "".join(random.choices(string.ascii_letters, k=10)),
            }
        ).insert()
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.outgoing_warehouse_name,
                "address": "".join(random.choices(string.ascii_letters, k=10)),
            }
        ).insert()
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.main_warehouse_name,
                "address": "".join(random.choices(string.ascii_letters, k=10)),
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
                    "quantity": random.randint(10, 15),
                    "rate": random.randint(100, 1000),
                }
            )

        # Test receiving items
        doc = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "entry_type": "Receipt",
                "target_warehouse": self.incoming_warehouse_name,
                "items": items,
            }
        )
        doc.insert()
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
                "quantity": random.randint(1, item["quantity"]),
                "rate": item["rate"],
            }
        doc = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "entry_type": "Transfer",
                "source_warehouse": self.incoming_warehouse_name,
                "target_warehouse": self.outgoing_warehouse_name,
                "items": items,
            }
        )
        doc.insert()
        created_stock_entry = frappe.get_doc("Stock Entry", doc.name)
        self.assertEqual(created_stock_entry.entry_type, "Transfer")

        for i, item in enumerate(items):
            items[i] = {
                "item": item["item"],
                "quantity": random.randint(1, item["quantity"]),
                "rate": random.randint(100, 1000),
            }
        doc = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "entry_type": "Consume",
                "source_warehouse": self.outgoing_warehouse_name,
                "items": items,
            }
        )
        doc.insert()
        created_stock_entry = frappe.get_doc("Stock Entry", doc.name)
        self.assertEqual(created_stock_entry.entry_type, "Consume")

    def test_create_guest(self):
        frappe.set_user("Guest")
        name = "".join(random.choices(string.ascii_letters, k=10))
        address = "".join(random.choices(string.ascii_letters, k=10))
        doc = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "stock_entry_name": name,
                "address": address,
            }
        )
        with self.assertRaises(frappe.exceptions.PermissionError):
            doc.insert()

    def test_read_guest(self):
        frappe.set_user("Guest")
        self.assertFalse(frappe.has_permission("Stock Entry"))
