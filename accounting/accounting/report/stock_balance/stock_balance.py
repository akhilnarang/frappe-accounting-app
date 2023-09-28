# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt
from datetime import datetime

from pydantic import BaseModel

import frappe
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

    # Get a combination of unique item-warehouse pairs from the ledger
    query_string = """
        SELECT DISTINCT item, warehouse
        FROM `tabStock Ledger Entry`
        WHERE entry_time BETWEEN %(from_date)s AND %(to_date)s
        """

    query_filters = {
        "from_date": filters.from_date.isoformat(),
        "to_date": filters.to_date.isoformat(),
    }

    if filters.item:
        query_string += " AND item = %(item)s"
        query_filters["item"] = filters.item

    if filters.warehouse:
        query_string += " AND warehouse = %(warehouse)s"
        query_filters["warehouse"] = filters.warehouse

    response: list[dict] = []

    item_warehouse_pairs: list[dict] = frappe.db.sql(query_string, query_filters, as_dict=True)
    for entry in item_warehouse_pairs:
        # Get opening stock
        if opening_stock := frappe.db.sql(
            """
            SELECT SUM(quantity) AS result
            FROM `tabStock Ledger Entry`
            WHERE entry_time < %(from_date)s
            AND item = %(item)s
            AND warehouse = %(warehouse)s
            """,
            {
                "from_date": filters.from_date.isoformat(),
                "item": entry["item"],
                "warehouse": entry["warehouse"],
            },
            as_dict=True,
        ):
            opening_stock = opening_stock[0].get("result", 0)

        # Get incoming stock
        if incoming_stock := frappe.db.sql(
            """
            SELECT SUM(quantity) AS result
            FROM `tabStock Ledger Entry`
            WHERE entry_time BETWEEN %(from_date)s AND %(to_date)s
            AND item = %(item)s
            AND warehouse = %(warehouse)s
            AND quantity > 0
            """,
            {
                "from_date": filters.from_date.isoformat(),
                "to_date": filters.to_date.isoformat(),
                "item": entry["item"],
                "warehouse": entry["warehouse"],
            },
            as_dict=True,
        ):
            incoming_stock = incoming_stock[0].get("result", 0)

        # Get outgoing stock
        if outgoing_stock := frappe.db.sql(
            """
            SELECT SUM(quantity) AS result
            FROM `tabStock Ledger Entry`
            WHERE entry_time BETWEEN %(from_date)s AND %(to_date)s
            AND item = %(item)s
            AND warehouse = %(warehouse)s
            AND quantity < 0
            """,
            {
                "from_date": filters.from_date.isoformat(),
                "to_date": filters.to_date.isoformat(),
                "item": entry["item"],
                "warehouse": entry["warehouse"],
            },
            as_dict=True,
        ):
            outgoing_stock = outgoing_stock[0].get("result", 0)

        # Get closing stock
        if closing_stock := frappe.db.sql(
            """
                SELECT SUM(quantity) AS result
                FROM `tabStock Ledger Entry`
                WHERE entry_time <= %(to_date)s
                AND item = %(item)s
                AND warehouse = %(warehouse)s
                """,
            {
                "to_date": filters.to_date.isoformat(),
                "item": entry["item"],
                "warehouse": entry["warehouse"],
            },
            as_dict=True,
        ):
            closing_stock = closing_stock[0].get("result", 0)

        # Get valuation rate
        if valuation_rate := frappe.db.sql(
            """
            SELECT AVG(rate) AS result
            FROM `tabStock Ledger Entry`
            WHERE entry_time between %(from_date)s AND %(to_date)s
            AND item = %(item)s
            AND warehouse = %(warehouse)s
            """,
            {
                "from_date": filters.from_date.isoformat(),
                "to_date": filters.to_date.isoformat(),
                "item": entry["item"],
                "warehouse": entry["warehouse"],
            },
            as_dict=True,
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
