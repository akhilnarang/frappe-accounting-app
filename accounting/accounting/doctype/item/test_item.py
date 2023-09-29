# Copyright (c) 2023, Akhil and Contributors
# See license.txt

import frappe
from accounting.utils import generate_random_string
from frappe.tests.utils import FrappeTestCase


def create_random_item(name: str | None = None):
	return frappe.new_doc(
		"Item",
		item_name=name or generate_random_string(),
	).insert()


class TestItem(FrappeTestCase):
	def test_create_item_without_mandatory_fields(self):
		frappe.set_user("Administrator")
		doc = frappe.new_doc("Item")
		with self.assertRaises(frappe.exceptions.ValidationError):
			doc.insert()

	def test_create_item(self):
		frappe.set_user("Administrator")
		name = generate_random_string()
		doc = create_random_item(name)
		created_doc_name = frappe.db.get_value("Item", {"item_name": name}, "name")
		self.assertEqual(doc.name, created_doc_name)

	def test_create_guest(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.exceptions.PermissionError):
			create_random_item()

	def test_read_guest(self):
		frappe.set_user("Guest")
		self.assertTrue(frappe.has_permission("Item"))
