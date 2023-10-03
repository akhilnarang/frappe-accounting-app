# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt
from datetime import datetime

from pydantic import BaseModel

import frappe
from frappe.query_builder import DocType, functions
from frappe.utils import flt


class Filters(BaseModel):
    item: str | None = None
    warehouse: str | None = None
    from_date: datetime
    to_date: datetime


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
            "fieldname": "opening_stock",
            "label": "Opening Stock",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "fieldname": "incoming_stock",
            "label": "Incoming Stock",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "fieldname": "outgoing_stock",
            "label": "Outgoing Stock",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "fieldname": "closing_stock",
            "label": "Closing Stock",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "fieldname": "valuation_rate",
            "label": "Valuation Rate",
            "fieldtype": "Float",
            "width": 200,
        },
    ]

    stock_ledger_entry = DocType("Stock Ledger Entry")
    query = frappe.qb.from_(stock_ledger_entry).distinct().select("item", "warehouse").where(
        stock_ledger_entry.entry_time.between(filters.from_date, filters.to_date)
    )

    if filters.item:
        query = query.where(stock_ledger_entry.item == filters.item)

    if filters.warehouse:
        query = query.where(stock_ledger_entry.warehouse == filters.warehouse)

    response: list[dict] = []

    item_warehouse_pairs: list[dict] = query.run(as_dict=True)
    for entry in item_warehouse_pairs:
        # Get opening stock
        if opening_stock := (frappe.qb.from_(stock_ledger_entry)
            .select(functions.Sum(stock_ledger_entry.quantity, "result"))
            .where(stock_ledger_entry.entry_time < filters.from_date)
            .where(stock_ledger_entry.item == entry["item"])
            .where(stock_ledger_entry.warehouse == entry["warehouse"])
            .run(as_dict=True)):
            opening_stock = opening_stock[0].get("result", 0)

        # Get incoming stock
        if incoming_stock := (frappe.qb.from_(stock_ledger_entry)
            .select(functions.Sum(stock_ledger_entry.quantity, "result"))
            .where(stock_ledger_entry.entry_time[filters.from_date:filters.to_date])
            .where(stock_ledger_entry.item == entry["item"])
            .where(stock_ledger_entry.warehouse == entry["warehouse"])
            .run(as_dict=True)):
            incoming_stock = incoming_stock[0].get("result", 0)

        # Get outgoing stock
        if outgoing_stock := (frappe.qb.from_(stock_ledger_entry)
            .select(functions.Sum(stock_ledger_entry.quantity, "result"))
            .where(stock_ledger_entry.entry_time[filters.from_date:filters.to_date])
            .where(stock_ledger_entry.item == entry["item"])
            .where(stock_ledger_entry.warehouse == entry["warehouse"])
            .run(as_dict=True)
        ):
            outgoing_stock = outgoing_stock[0].get("result", 0)

        # Get closing stock
        if closing_stock := (frappe.qb.from_(stock_ledger_entry)
            .select(functions.Sum(stock_ledger_entry.quantity, "result"))
            .where(stock_ledger_entry.entry_time <= filters.to_date)
            .where(stock_ledger_entry.item == entry["item"])
            .where(stock_ledger_entry.warehouse == entry["warehouse"])
            .run(as_dict=True)
        ):
            closing_stock = closing_stock[0].get("result", 0)

        # Get valuation rate
        if valuation_rate := (frappe.qb.from_(stock_ledger_entry)
            .select(functions.Avg(stock_ledger_entry.rate, "result"))
            .where(stock_ledger_entry.entry_time[filters.from_date:filters.to_date])
            .where(stock_ledger_entry.item == entry["item"])
            .where(stock_ledger_entry.warehouse == entry["warehouse"])
            .run(as_dict=True)
        ):
            valuation_rate = valuation_rate[0].get("result", 0)

        response.append(
            {
                "item": entry["item"],
                "warehouse": entry["warehouse"],
                "opening_stock": flt(opening_stock),
                "incoming_stock": flt(incoming_stock),
                "outgoing_stock": abs(flt(outgoing_stock)),
                "closing_stock": flt(closing_stock),
                "valuation_rate": flt(valuation_rate),
            }
        )
    return columns, response
