# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt
import itertools
from typing import Callable

from pydantic import BaseModel

import frappe
from frappe import cint
from frappe.model.document import Document


class LedgerEntry(BaseModel):
	item: str
	warehouse: str
	quantity: float
	rate: float


class StockEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from accounting.accounting.doctype.stock_entry_item.stock_entry_item import StockEntryItem
		from frappe.types import DF

		amended_from: DF.Link | None
		entry_type: DF.Literal['Receipt', 'Consume', 'Transfer']
		items: DF.Table[StockEntryItem]
		source_warehouse: DF.Link
		target_warehouse: DF.Link
	# end: auto-generated types
	def validate_item_metadata(self, item: "StockEntryItem"):
		if item.quantity <= 0:
			frappe.throw("Quantity needs to be a positive number")

		if item.rate is None:
			frappe.throw("Rate is mandatory")

	def validate_receipt(self, item: "StockEntryItem"):
		if not self.target_warehouse and not item.target_warehouse:
			frappe.throw("Target Warehouse is mandatory for receipt")
		elif self.target_warehouse:
			item.target_warehouse = self.target_warehouse

		if self.source_warehouse or item.source_warehouse:
			frappe.throw("Source Warehouse is not allowed for receipt")

	def validate_consume(self, item: "StockEntryItem"):
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

	def validate_transfer(self, item: "StockEntryItem"):
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

	def insert_ledger(self, items: list[LedgerEntry]):
		for row in items:
			frappe.new_doc(
				"Stock Ledger Entry",
				item=row.item,
				warehouse=row.warehouse,
				entry_time=self.current_time,
				quantity=row.quantity,
				rate=row.rate,
				type="Stock Entry",
				source=self.name,
			).insert()

	def handle_invalid_entry_type(self, _):
		frappe.throw(f"Invalid Entry Type: {self.entry_type}")

	def before_save(self):
		self.current_time = frappe.utils.now_datetime()
		validation_func: Callable[["StockEntryItem"], None] = self.handle_invalid_entry_type
		match self.entry_type:
			case "Receipt":
				validation_func = self.validate_receipt
			case "Consume":
				validation_func = self.validate_consume
			case "Transfer":
				validation_func = self.validate_transfer

		for item in self.items:
			self.validate_item_metadata(item)
			validation_func(item)

	def on_submit(self):
		self.current_time = frappe.utils.now_datetime()
		items: list[LedgerEntry] = []
		match self.entry_type:
			case "Receipt":
				items.extend(
					[
						LedgerEntry(
							item=item.item,
							warehouse=item.target_warehouse,
							quantity=item.quantity,
							rate=item.rate
						)
						for item in self.items
					]
				)
			case "Consume":
				items.extend(
					[
						LedgerEntry(
							item=item.item,
							warehouse=item.source_warehouse,
							quantity=-item.quantity,
							rate=item.rate
						)
						for item in self.items
					]
				)
			case "Transfer":
				items.extend(
					itertools.chain.from_iterable(
						(
							LedgerEntry(
								item=item.item,
								warehouse=item.source_warehouse,
								quantity=-item.quantity,
								rate=item.rate
							),
							LedgerEntry(
								item=item.item,
								warehouse=item.target_warehouse,
								quantity=item.quantity,
								rate=item.rate
							)
						)
						for item in self.items
					)
				)

		self.insert_ledger(items)

	def on_cancel(self):
		self.current_time = frappe.utils.now_datetime()
		items: list[LedgerEntry] = []

		match self.entry_type:
			case "Receipt":
				items.extend(
					[
						LedgerEntry(
							item=item.item,
							warehouse=item.target_warehouse,
							quantity=-item.quantity,
							rate=item.rate
						)
						for item in self.items
					]
				)
			case "Consume":
				items.extend(
					[
						LedgerEntry(
							item=item.item,
							warehouse=item.source_warehouse,
							quantity=item.quantity,
							rate=item.rate
						)
						for item in self.items
					]
				)
			case "Transfer":
				items.extend(
					itertools.chain.from_iterable(
						(
							LedgerEntry(
								item=item.item,
								warehouse=item.source_warehouse,
								quantity=item.quantity,
								rate=item.rate
							),
							LedgerEntry(
								item=item.item,
								warehouse=item.target_warehouse,
								quantity=-item.quantity,
								rate=item.rate
							)
						)
						for item in self.items
					)
				)

		self.insert_ledger(items)
