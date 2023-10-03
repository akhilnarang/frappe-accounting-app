// Copyright (c) 2023, Akhil and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Ledger"] = {
	"filters": [
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			"get_query": function () {
				return frappe.db.get_list("Item");
			}
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Warehouse",
			"get_query": function () {
				return frappe.db.get_list("Warehouse");
			}
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Datetime",
			"width": "80",
			"default": frappe.datetime.add_months(frappe.datetime.now_datetime(), -1),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Datetime",
			"width": "80",
			"default": frappe.datetime.now_datetime()
		}
	]
};
