# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt

from datetime import datetime

from pydantic import BaseModel

import frappe
from frappe.query_builder import DocType


class Filters(BaseModel):
	item: str | None = None
	warehouse: str | None = None
	from_date: datetime | None = None
	to_date: datetime | None = None


def execute(incoming_filters: dict) -> tuple[list[dict], list[dict]]:
	filters = Filters.model_validate(incoming_filters)
	columns = [
		{
			"fieldname": "item",
			"label": "Item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 200,
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 200,
		},
		{
			"fieldname": "entry_time",
			"label": "Entry Time",
			"fieldtype": "DateTime",
			"width": 200,
		},
		{
			"fieldname": "quantity",
			"label": "Quantity",
			"fieldtype": "Float",
			"width": 200,
		},
		{
			"fieldname": "rate",
			"label": "Rate",
			"fieldtype": "Float",
			"width": 200,
		},
	]

	stock_ledger_entry = DocType("Stock Ledger Entry")
	query = frappe.qb.from_(stock_ledger_entry).select("*")

	if filters.item:
		query = query.where(stock_ledger_entry.item == filters.item)

	if filters.warehouse:
		query = query.where(stock_ledger_entry.warehouse == filters.warehouse)

	if filters.from_date and filters.to_date:
		query = query.where(stock_ledger_entry.entry_time[filters.from_date:filters.to_date])
	elif filters.from_date:
		query.where(stock_ledger_entry.entry_time >= filters.from_date)
	elif filters.to_date:
		query.where(stock_ledger_entry.entry_time <= filters.to_date)

	data = query.run()
	return columns, data
