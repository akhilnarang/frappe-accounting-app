// Copyright (c) 2023, Akhil and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Ledger Entry", {
	refresh(frm) {
		// Since we only support `Stock Entry` for now, we set the value and make it read-only
		frm.set_value("type", "Stock Entry")
		frm.set_df_property("type", "read_only", 1)
	},
});
