// frappe.ui.form.on('BPCL Company', {
//     refresh: function(frm) {
//         frm.add_custom_button(__('Register Vehicle'), function() {

//             let d = new frappe.ui.Dialog({
//                 title: 'Register Vehicle',
//                 fields: [
//                     {
//                         fieldname: 'vehicle_no',
//                         fieldtype: 'Table',
//                         label: 'Vehicles',
//                         cannot_add_rows: false,
//                         in_place_edit: true,
//                         reqd: 1,
//                         fields: [
//                             {
//                                 fieldtype: 'Link',
//                                 fieldname: 'vehicle_list',
//                                 options: 'Vehicle',
//                                 label: 'Vehicle No',
//                                 in_list_view: true,
//                                 reqd: 1
//                             }
//                         ]
//                     }
//                 ],
//                 primary_action_label: 'Submit',
//                 primary_action(values) {
//                     if (!values.vehicle_no || values.vehicle_no.length === 0) {
//                         frappe.msgprint(__('Please add at least one Vehicle.'));
//                         return;
//                     }

//                     let vehicle_list = values.vehicle_no.map(row => row.vehicle_list);

//                     frappe.call({
//                         method: "transport.transport.doctype.bpcl_company.bpcl_company.register_vehicles",
//                         args: {
//                             vehicle_list: vehicle_list,
//                             // bpcl_company: frm.doc.name,
//                             company_id: frm.doc.name
//                         },
//                         callback: function(r) {
//                             if (!r.exc) {
//                                 frappe.msgprint(__('Vehicles registered successfully'));
//                                 d.hide();
//                                 frm.reload_doc();
//                             }
//                         }
//                     });
//                 }
//             });

//             d.show();
//         });
//     }
// });



frappe.ui.form.on('BPCL Company', {
    refresh: function (frm) {
        frm.add_custom_button(__('Register Vehicle'), function () {
            let d = new frappe.ui.Dialog({
                title: 'Register Vehicle',
                fields: [
                    {
                        fieldname: 'vehicle_no',
                        fieldtype: 'Table',
                        label: 'Vehicles',
                        cannot_add_rows: false,
                        in_place_edit: true,
                        reqd: 1,
                        fields: [
                            {
                                fieldtype: 'Link',
                                fieldname: 'vehicle_list',
                                options: 'Vehicle',
                                label: 'Vehicle No',
                                in_list_view: true,
                                reqd: 1
                            }
                        ]
                    }
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    if (!values.vehicle_no || values.vehicle_no.length === 0) {
                        frappe.msgprint(__('Please add at least one Vehicle.'));
                        return;
                    }

                    const vehicle_list = values.vehicle_no.map(row => row.vehicle_list);

                    frappe.call({
                        method: "transport.transport.doctype.bpcl_company.bpcl_company.register_vehicles",
                        args: {
                            vehicle_list: JSON.stringify(vehicle_list),
                            company_id: frm.doc.company_id // doc.name used as parent tree node'
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint(__('Vehicles registered successfully'));
                                d.hide();
                                frm.reload_doc();
                            }
                        }
                    });
                }
            });

            d.show();
        });
    }
});



// change pin request button





frappe.ui.form.on('BPCL Company', {
    refresh: function(frm) {
        if (!frm.doc.is_group && frm.doc.card_no) {
            frm.add_custom_button('Change PIN', () => {
                const d = new frappe.ui.Dialog({
                    title: 'Change Fleet Card PIN',
                    fields: [
                        {
                            label: 'Card Number',
                            fieldname: 'card_no',
                            fieldtype: 'Data',
                            default: frm.doc.card_no,
                            read_only: 1
                        },
                        {
                            label: 'Old PIN',
                            fieldname: 'old_pin',
                            fieldtype: 'Data',
                            default: frm.doc.pin,
                            read_only: 1
                        },
                        {
                            label: 'New PIN',
                            fieldname: 'new_pin',
                            fieldtype: 'Data',
                            reqd: 1
                        }
                    ],
                    primary_action_label: 'Change PIN',
                    primary_action(values) {
                        frappe.call({
                            method: 'transport.transport.doctype.bpcl_company.bpcl_company.change_fleet_card_pin',
                            args: {
                                card_no: values.card_no,
                                old_pin: values.old_pin,
                                new_pin: values.new_pin
                            },
                            freeze: true,
                            callback(r) {
                                if (r.message) {
                                    frappe.msgprint(r.message);
                                    d.hide();
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });

                d.show();
            });
        }
    }
});

