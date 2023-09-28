# Copyright (c) 2023, Akhil and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from ..item.test_item import create_random_item
from ..stock_entry.test_stock_entry import create_entry as create_stock_entry
from ..warehouse.test_warehouse import create_random_warehouse
from ....utils import get_random_integer


class TestStockLedgerEntry(FrappeTestCase):
    def test_ledger(self):
        frappe.set_user("Administrator")
        item = create_random_item()
        warehouse_1 = create_random_warehouse()
        quantity = get_random_integer()
        rate = get_random_integer(minimum=100, maximum=500)
        create_stock_entry(
            entry_type="Receipt",
            items=[
                {
                    "item": item.name,
                    "quantity": quantity,
                    "rate": rate,
                }
            ],
            source_warehouse=None,
            target_warehouse=warehouse_1.name,
        )
        doc = frappe.db.get(
            "Stock Ledger Entry", {"item": item.name, "warehouse": warehouse_1.name}
        )
        self.assertEqual(doc.item, item.name)
        self.assertEqual(doc.warehouse, warehouse_1.name)
        self.assertEqual(doc.quantity, quantity)
        self.assertEqual(doc.rate, rate)

        warehouse_2 = create_random_warehouse()
        create_stock_entry(
            entry_type="Transfer",
            items=[
                {
                    "item": item.name,
                    "quantity": quantity,
                    "rate": rate,
                }
            ],
            source_warehouse=warehouse_1.name,
            target_warehouse=warehouse_2.name,
        )

        doc = frappe.db.get(
            "Stock Ledger Entry", {"item": item.name, "warehouse": warehouse_2.name}
        )
        self.assertEqual(doc.item, item.name)
        self.assertEqual(doc.warehouse, warehouse_2.name)
        self.assertEqual(doc.quantity, quantity)
        self.assertEqual(doc.rate, rate)

        # Check that the ledger entry for the source warehouse shows the negative
        doc = frappe.db.get_list(
            "Stock Ledger Entry",
            {"item": item.name, "warehouse": warehouse_1.name},
            filters=["quantity"],
            order_by="creation asc",
        )
        self.assertEqual(len(doc), 2)
        self.assertEqual(doc[0].quantity, quantity)
        self.assertEqual(doc[1].quantity, -quantity)
        self.assertEqual(sum([d.quantity for d in doc]), 0)

        create_stock_entry(
            entry_type="Consume",
            items=[
                {
                    "item": item.name,
                    "quantity": quantity,
                    "rate": rate,
                }
            ],
            source_warehouse=warehouse_2.name,
            target_warehouse=None,
        )

        doc = frappe.db.get_list(
            "Stock Ledger Entry",
            {"item": item.name, "warehouse": warehouse_2.name},
            filters=["quantity"],
            order_by="creation asc",
        )
        self.assertEqual(len(doc), 2)
        self.assertEqual(doc[0].quantity, quantity)
        self.assertEqual(doc[1].quantity, -quantity)
        self.assertEqual(sum([d.quantity for d in doc]), 0)
