console.log("BPCL Company listview js loaded!");

frappe.listview_settings['BPCL Company'] = {
    onload: function(listview) {
        console.log("Custom listview for BPCL Company loaded");

        listview.page.add_inner_button(__('Register Company'), () => {
            console.log("Register Company button clicked");

            let d = new frappe.ui.Dialog({
                title: 'Register Transport Company',
                fields: [
                    { label: 'Name', fieldname:  'company_name', fieldtype: 'Data', reqd: 1 },
                    { label: 'Email', fieldname: 'email', fieldtype: 'Data', reqd: 1 },
                    { label: 'Phone', fieldname: 'phone', fieldtype: 'Data', reqd: 1 },
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: 'transport.transport.doctype.bpcl_company.bpcl_company.send_to_bunk',
                        args: values,
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Details sent to bunk company successfully!'));
                                console.log("API Response:", r.message);
                                d.hide();
                            }
                        }
                    });
                }
            });
            d.show();
        });
    }
};
