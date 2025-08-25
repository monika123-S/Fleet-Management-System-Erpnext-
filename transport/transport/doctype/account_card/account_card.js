// Copyright (c) 2025, Monika and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Account_card", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Account_card', {
    refresh: function(frm) {
        frm.add_custom_button(__('Register Vehicle'), function() {

            // Ensure MultiSelectDialog is available
            if (!frappe.ui.form.MultiSelectDialog) {
                frappe.msgprint(__('MultiSelectDialog not found. Please check your Frappe version.'));
                return;
            }

            // Open MultiSelectDialog
            new frappe.ui.form.MultiSelectDialog({
                doctype: "Vehicle",
                target: frm,
                setters: {},
                add_filters_group: 1,
                allow_multiple: 1,
                size: 'extra-large',
                primary_action_label: "Register",
                action(selections) {
                    if (!selections || selections.length === 0) {
                        frappe.msgprint(__('Please select at least one vehicle.'));
                        return;
                    }

                    frappe.call({
                        method: "fm.fuel_management.api.create_fleet_card",
                        type: "POST",
                        args: {
                            account_card: frm.doc.name,
                            vehicles: selections
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('API called successfully for vehicles: ') + selections.join(', '));
                            }
                        }
                    });

                    this.dialog.hide();
                }
            });

        });
    }
});

