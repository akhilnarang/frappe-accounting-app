# Copyright (c) 2023, Akhil and Contributors
# See license.txt
import random
import string

import frappe
from frappe.tests.utils import FrappeTestCase


class TestItem(FrappeTestCase):
	def test_create_item_without_mandatory_fields(self):
		frappe.set_user("Administrator")
		doc = frappe.get_doc({
			"doctype": "Item",
		})
		with self.assertRaises(frappe.exceptions.MandatoryError):
			doc.insert()

	def test_create_item(self):
		frappe.set_user("Administrator")
		name = ''.join(random.choices(string.ascii_letters, k=10))
		available_quantity = random.choice(range(100))
		doc = frappe.get_doc({
			"doctype": "Item",
			"item_name": name,
			"available_quantity": available_quantity
		})
		doc.insert()
		assert doc.item_name == name
		assert doc.available_quantity == available_quantity


	def test_create_guest(self):
		frappe.set_user("Guest")
		name = ''.join(random.choices(string.ascii_letters, k=10))
		available_quantity = random.choice(range(100))
		doc = frappe.get_doc({
			"doctype": "Item",
			"item_name": name,
			"available_quantity": available_quantity
		})
		with self.assertRaises(frappe.exceptions.PermissionError):
			doc.insert()

	def test_read_guest(self):
		frappe.set_user("Guest")
		self.assertTrue(frappe.has_permission("Item"))