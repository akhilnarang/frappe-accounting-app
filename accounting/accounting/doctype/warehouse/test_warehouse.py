# Copyright (c) 2023, Akhil and Contributors
# See license.txt

import frappe
from accounting.utils import generate_random_string
from frappe.tests.utils import FrappeTestCase


def create_random_warehouse(name: str | None = None, address: str | None = None):
	return frappe.new_doc(
		"Warehouse",
		warehouse_name=name or generate_random_string(),
		address=address or generate_random_string(),
	).insert()


class TestWarehouse(FrappeTestCase):
	def test_create_warehouse_without_mandatory_fields(self):
		frappe.set_user("Administrator")
		doc = frappe.new_doc("Warehouse")
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.insert()

	def test_create_warehouse(self):
		frappe.set_user("Administrator")
		name = generate_random_string()
		doc = create_random_warehouse(name)
		self.assertEqual(
			doc.name, frappe.db.get_value("Warehouse", {"warehouse_name": name}, "name")
		)

	def test_create_guest(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.exceptions.PermissionError):
			create_random_warehouse()

	def test_read_guest(self):
		frappe.set_user("Guest")
		self.assertFalse(frappe.has_permission("Warehouse"))
