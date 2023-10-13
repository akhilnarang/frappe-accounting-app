# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockEntryItem(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        item: DF.Link
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        quantity: DF.Float
        rate: DF.Int
        source_warehouse: DF.Link | None
        target_warehouse: DF.Link | None
    # end: auto-generated types
    pass
