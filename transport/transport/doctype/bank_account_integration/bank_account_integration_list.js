

frappe.listview_settings['Bank Account Integration'] = {
    onload: function(listview) {
        console.log("Custom listview for Bank Account Integration loaded");

        listview.page.add_inner_button(__('Register Bank'), () => {
            console.log("Register Company button clicked");

            let d = new frappe.ui.Dialog({
                title: 'Register Bank Account',
                fields: [
                    { label: 'Account Name', fieldname:  'account_name', fieldtype: 'Data', reqd: 1 },
                    { label: 'Phone', fieldname: 'phone', fieldtype: 'Data', reqd: 1 },
                    { label: 'Address', fieldname: 'address', fieldtype: 'Data', reqd: 1 },
                    {label: 'Email', fieldname: 'email', fieldtype: 'Data', reqd: 1 },
                    { label: 'Account Type', fieldname: 'account_type', fieldtype: 'Select', options: ['Savings', 'Current'], reqd: 1 },
                    // { label: 'Client Public Key File', fieldname: 'client_public_key_file', fieldtype: 'Text', reqd: 1 }
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: 'transport.transport.doctype.bank_account_integration.bank_account_integration.send_account_bank',
                        args: values,
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Details sent to bank company successfully!'));
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
