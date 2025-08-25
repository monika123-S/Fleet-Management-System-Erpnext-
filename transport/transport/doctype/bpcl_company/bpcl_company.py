import frappe
import requests
from frappe.model.document import Document
from frappe import _
import json
import re

class BPCLCompany(Document):
    def autoname(self):
        if self.is_group:
            self.name = self.get_next_name(prefix="ACC-")
        else:
            self.name = self.get_next_name(prefix="CARD-")

    def get_next_name(self, prefix):
        last = frappe.db.sql(f"""
            SELECT name FROM `tabBPCL Company`
            WHERE name LIKE '{prefix}%'
            ORDER BY CAST(SUBSTRING(name, {len(prefix)+1}) AS UNSIGNED) DESC
            LIMIT 1
        """, as_dict=True)
        if last:
            last_number = int(last[0]["name"].split(prefix)[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        return f"{prefix}{next_number:05d}"





@frappe.whitelist()
def send_to_bunk(company_name, email, phone):
    url = "http://192.168.1.38:8000/api/method/fm.fuel_management.api.onboard_transport_company"
    data = {"company_name": company_name, "email": email, "phone": phone}
    res = requests.post(url, json=data)

    if res.status_code == 200:
        response_data = res.json().get("message", {})
        print("Raw Response:", response_data)

        doc = frappe.new_doc("BPCL Company")
        doc.company_name = company_name
        doc.email = email
        doc.phone = phone
        doc.password = response_data.get("password")
        doc.company_id = response_data.get("company_id")
        doc.wallet_id = response_data.get("wallet_id")
        doc.is_group=1
        doc.insert()

        doc=frappe.new_doc("Company")
        doc.company_name = company_name
        doc.default_currency = "INR"
        doc.company_abbr = company_name[:3].upper()  # First 3 letters
        doc.insert()

        return {
            "message": "Details sent to bunk company successfully!",
        }
    else:
        return {"message": f"Failed: {res.status_code} {res.text}"}
    
# @frappe.whitelist()
# def send_to_bunk(company_name, email, phone):
#     print("working")

#     url = "http://192.168.1.38/api/method/fm.fuel_management.api.onboard_transport_company"

#     print("URL:", url)


#     payload = {"company_name": company_name, "email": email, "phone": phone}
#     print("Payload:", payload)

#     try:
#         print("helooooooooooo")
#         res = requests.post(url, json=payload)
#         print("Response:", res)
#         print("Response Status Code:", res.status_code)


#         if res.status_code == 500:
#             print("Server Error 500:", res.text)
#             return {"message": "Server Error 500: " + res.text}
        
#         if res.status_code == 404:
#             print("Not Found 404:", res.text)
#             return {"message": "Not Found 404: " + res.text}    
#         if res.status_code == 417:
#             print("Expectation Failed 417:", res.text)
#             return {"message": "Expectation Failed 417: " + res.text}
        

#         if res.status_code == 200:
#             print("Success Response")
#             response_json = res.json()
#             print("Raw Response:", response_json)

#             message = response_json.get("message", {})
#             print("mmmmmmmmm",message)
#             #data = message.get("data", {})
#             #print("Data from response:", data)

#             doc = frappe.new_doc("BPCL Company")
#             doc.company_name = company_name
#             doc.email = email  # from input
#             doc.phone = phone  # from input
#             doc.wallet_id = message.get("wallet_id")
#             doc.password = message.get("password")
#             doc.company_id = message.get("company_id")
#             doc.is_group = 1 

#             print("Wallet ID:", doc.wallet_id, 'wallet_id')
#             print("Company ID:", doc.company_id, 'company_id')
#             print("Password:", doc.password, 'password')

#             doc.insert()


#             doc=frappe.new_doc("Company")
#             doc.company_name = company_name
#             doc.default_currency = "INR"
#             doc.company_abbr = company_name[:3].upper()  # First 3 letters
#             doc.insert()


#             return {
#                 "message": "Details sent to bunk company successfully!",
#             }

#         else:
#             return {"message": f"Failed: {res.status_code} {res.text}"}

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "Bunk API Error")
#         return {"message": "Error occurred"}


# next need to login and get the session cookies 



def get_session_cookies(email):
    company = frappe.get_doc("BPCL Company", {"email": email})
    print("cccccccccccc",company)
    email = company.email
    password = company.password

    print("Using Email:", email)
    print("Using Password:", password)

    login_url = "http://192.168.1.38:8000/api/method/login"
    response = requests.post(login_url, data={"usr": email, "pwd": password})

    print("Login response:", response.text)

    if response.status_code == 200:
        cookies = response.cookies.get_dict()
        frappe.cache().hset("bpcl_cookies", email, cookies)
        return cookies
    else:
        frappe.throw("Login failed: " + response.text)

@frappe.whitelist()
def register_vehicles(vehicle_list, company_id):

    print("vechiclelist:",vehicle_list)
    print("company_id:",company_id)
    try:
        vehicle_list = json.loads(vehicle_list)
        vehicles = [v.strip() for v in vehicle_list if isinstance(v, str) and v.strip()]
    except Exception as e:
        frappe.throw(_("Invalid vehicle list format: ") + str(e))

    if not vehicles:
        frappe.throw(_("No valid vehicle numbers found."))

    # Fetch parent BPCL Company
    parent_docs = frappe.get_all("BPCL Company", filters={"company_id": company_id}, fields=["name", "company_id"])
    print("Matching companies:", parent_docs)

    if not parent_docs:
        frappe.throw(_("Could not find Parent BPCL Company: {0}").format(company_id))

    parent_company = frappe.get_doc("BPCL Company", parent_docs[0]["name"])


    email = parent_company.email
    print("emaill:",email)
    password = parent_company.password

    cookies = get_session_cookies(email)
    print(f"Cookies obtained: {cookies}")
    api_url = "http://192.168.1.38:8000/api/method/fm.fuel_management.api.create_fleet_card"
    payload = {
        "vehicle_list": vehicles,
        "company_id": company_id
    }
    print(payload)
    response = requests.post(api_url, json=payload, cookies=cookies)
    print("rrrrrrrrrrrrrrrr",response)

    try:
        response.raise_for_status()
        response_json = response.json()
        print("Full API Response:", response_json)
        # card_details = response_json.get("message", {}).get("card_details", [])
        #card_details = response_json.get("message", {}).get("data", {}).get("card_details", [])
        card_details = response_json.get("message", {}).get("card_details", [])

        print("card_details:", card_details)
    except Exception as e:
        frappe.throw(_("Failed to retrieve card details: ") + str(e))


    created_docs = []

    for card in card_details:
        vehicle_no = card.get("vehicle_no", "").strip()
        if not vehicle_no:
            frappe.logger().warning("Empty vehicle_no, skipping.")
            continue
        existing = frappe.get_all("BPCL Company", filters={
            "vehicle_list": vehicle_no,
            "parent_bpcl_company": company_id,
            "is_group": 0
        })
        if existing:
            frappe.logger().info(f"Vehicle {vehicle_no} already exists under {company_id}. Skipping.")
            continue

    #     try:
    #         doc = frappe.new_doc("BPCL Company")
    #         doc.vehicle_list = card.get("vehicle_no")
    #         doc.card_no = card.get("card_no")
    #         doc.pin = card.get("pin")
    #         doc.parent_bpcl_company = company_id
    #         doc.is_group = 0   # Important for autoname logic to detect it's a child


    #         doc.insert(ignore_permissions=True)
    #         created_docs.append(doc.name)

    #     except Exception as e:
    #         frappe.logger().error(f"Failed to create Fleet Card for {vehicle_no}: {str(e)}")
    #         continue

    # return {
    #     "message": f"Processed {len(created_docs)} vehicle(s).",
    #     "created_docs": created_docs
    # }

        print("Attempting to create doc with:")
        print("Vehicle No:", vehicle_no)
        print("Card No:", card.get("card_no"))
        print("Parent Company ID:", company_id)

        try:
            doc = frappe.new_doc("BPCL Company")
            doc.vehicle_list = card.get("vehicle_no")
            doc.card_no = card.get("card_no")
            doc.pin = card.get("pin")
            # doc.parent_bpcl_company = company_id
            doc.parent_bpcl_company = parent_company.name
            doc.is_group = 0
            print("Doc contents before insert:", doc.as_dict())

            doc.insert(ignore_permissions=True)
            print("Doc inserted with name:", doc.name)

            created_docs.append(doc.name)

        except Exception as e:
            print(f"Error inserting doc: {str(e)}")






# next to request for changing password 

@frappe.whitelist()
def change_fleet_card_pin(card_no, old_pin, new_pin):
    parent_docs = frappe.get_all(
        "BPCL Company",
        filters={"card_no": card_no, "is_group": 0},
        fields=["name", "parent_bpcl_company"]
    )
    print("mmmmmmmmmmmmmm",parent_docs)

    if not parent_docs:
        frappe.throw(_("Could not find BPCL Company for Card No: {0}").format(card_no))

    parent_company_name = parent_docs[0]["parent_bpcl_company"]
    print("kkkkkkkkkkkkkk", parent_company_name)
    parent_company = frappe.get_doc("BPCL Company", parent_company_name)
    print("Parent Company:", parent_company)
    email = parent_company.email

    if not email:
        frappe.throw(_("No email found on parent BPCL Company: {0}").format(parent_company_name))
    cookies = get_session_cookies(email)
    print("ccccccccccccc", cookies)
    url = "http://192.168.1.38:8000/api/method/fm.fuel_management.api.change_card_pin"

    payload = {
        "card_no": card_no,
        "old_pin": old_pin,
        "new_pin": new_pin
    }
    print("pppppppppp", payload)

    try:
        response = requests.post(url, json=payload, cookies=cookies)
        response.raise_for_status()

        res_json = response.json()
        print("eeeeeeeee", res_json)

        if res_json.get("message", {}).get("status") == "success":
            frappe.db.set_value(
                "BPCL Company",
                parent_docs[0]["name"],  
                "pin",
                new_pin
            )
            frappe.db.commit()

            return {
                "message": "PIN changed successfully!"
            }
        else:
            return {
                "message": f"Failed to change PIN: {res_json.get('message')}"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Change Fleet Card PIN Error")
        return {
            "message": "An unexpected error occurred while changing PIN."
        }





