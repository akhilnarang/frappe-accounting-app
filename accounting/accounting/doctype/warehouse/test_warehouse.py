# Copyright (c) 2023, Akhil and Contributors
# See license.txt
import random
import string

import frappe
from frappe.tests.utils import FrappeTestCase


class TestWarehouse(FrappeTestCase):
    def test_create_warehouse_without_mandatory_fields(self):
        frappe.set_user("Administrator")
        doc = frappe.get_doc(
            {
                "doctype": "Warehouse",
            }
        )
        with self.assertRaises(frappe.exceptions.ValidationError):
            doc.insert()

    def test_create_warehouse(self):
        frappe.set_user("Administrator")
        name = "".join(random.choices(string.ascii_letters, k=10))
        address = "".join(random.choices(string.ascii_letters, k=10))
        doc = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": name,
                "address": address,
            }
        )
        doc.insert()
        created_warehouse = frappe.get_doc("Warehouse", doc.name)
        self.assertEqual(created_warehouse.warehouse_name, name)
        self.assertEqual(created_warehouse.address, address)

    def test_create_guest(self):
        frappe.set_user("Guest")
        name = "".join(random.choices(string.ascii_letters, k=10))
        address = "".join(random.choices(string.ascii_letters, k=10))
        doc = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": name,
                "address": address,
            }
        )
        with self.assertRaises(frappe.exceptions.PermissionError):
            doc.insert()

    def test_read_guest(self):
        frappe.set_user("Guest")
        self.assertFalse(frappe.has_permission("Warehouse"))
