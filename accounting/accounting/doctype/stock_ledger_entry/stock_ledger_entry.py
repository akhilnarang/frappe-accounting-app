# Copyright (c) 2023, Akhil and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class StockLedgerEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		entry_time: DF.Datetime
		item: DF.Link
		quantity: DF.Int
		rate: DF.Int
		warehouse: DF.Link
	# end: auto-generated types
	pass
