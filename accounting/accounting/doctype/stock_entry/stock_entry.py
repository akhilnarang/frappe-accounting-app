# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt

import frappe
from accounting.accounting.doctype.stock_entry_table_item.stock_entry_table_item import (
	StockEntryTableItem,
)
from frappe import cint
from frappe.model.document import Document


class StockEntry(Document):
	def validate_item_metadata(self, item: StockEntryTableItem):
		if item.quantity < 1:
			frappe.throw("Quantity needs to be a positive number")

		if item.rate is None:
			frappe.throw("Rate is mandatory")

	def validate_receipt(self, item: StockEntryTableItem):
		if not self.target_warehouse and not item.target_warehouse:
			frappe.throw("Target Warehouse is mandatory for receipt")
		elif self.target_warehouse:
			item.target_warehouse = self.target_warehouse

		if self.source_warehouse or item.source_warehouse:
			frappe.throw("Source Warehouse is not allowed for receipt")

	def validate_consume(self, item: StockEntryTableItem):
		if not item.source_warehouse and not self.source_warehouse:
			frappe.throw("Source Warehouse is mandatory for consume")
		elif self.source_warehouse:
			item.source_warehouse = self.source_warehouse

		if item.target_warehouse or self.target_warehouse:
			frappe.throw("Target Warehouse is not allowed for consume")

		# Fetch the stock for the given item in the given warehouse
		stock = frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item": item.item,
				"warehouse": item.source_warehouse,
			},
			"sum(quantity)",
		)

		# Ensure that the warehouse has enough stock
		if item.quantity > cint(stock):
			frappe.throw(
				f"Not enough stock in the warehouse - available: {stock or 0}, requested: {item.quantity}"
			)

	def validate_transfer(self, item: StockEntryTableItem):
		if not self.target_warehouse and not item.target_warehouse:
			frappe.throw("Target Warehouse is mandatory for transfer")
		elif self.target_warehouse:
			item.target_warehouse = self.target_warehouse

		if not item.source_warehouse and not self.source_warehouse:
			frappe.throw("Source Warehouse is not allowed for transfer")
		elif self.source_warehouse:
			item.source_warehouse = self.source_warehouse

		if item.source_warehouse == item.target_warehouse:
			frappe.throw("Source and Target Warehouse cannot be the same")

		# Fetch the stock for the given item in the given warehouse
		stock = frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item": item.item,
				"warehouse": item.source_warehouse,
			},
			"sum(quantity)",
		)

		# Ensure that the warehouse has enough stock
		if item.quantity > cint(stock):
			frappe.throw(
				f"Not enough stock in the warehouse - available: {stock or 0}, requested: {item.quantity}"
			)

		# Get the average rate for the given item in the given warehouse
		if average_rate := frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item": item.item,
				"warehouse": item.source_warehouse,
			},
			"avg(rate)",
		):
			item.rate = average_rate

	def insert_ledger(self, item: str, warehouse: str, quantity: int, rate: float):
		frappe.get_doc(
			{
				"doctype": "Stock Ledger Entry",
				"item": item,
				"warehouse": warehouse,
				"entry_time": self.current_time,
				"quantity": quantity,
				"rate": rate,
			}
		).insert()

	def before_save(self):
		self.current_time = frappe.utils.now_datetime()
		match self.entry_type:
			case "Receipt":
				for item in self.items:
					self.validate_item_metadata(item)
					self.validate_receipt(item)
					self.insert_ledger(item.item, item.target_warehouse, item.quantity, item.rate)
			case "Consume":
				for item in self.items:
					self.validate_item_metadata(item)
					self.validate_consume(item)
					self.insert_ledger(item.item, item.source_warehouse, -item.quantity, item.rate)
			case "Transfer":
				for item in self.items:
					self.validate_item_metadata(item)
					self.validate_transfer(item)
					self.insert_ledger(item.item, item.source_warehouse, -item.quantity, item.rate)
					self.insert_ledger(item.item, item.target_warehouse, item.quantity, item.rate)
