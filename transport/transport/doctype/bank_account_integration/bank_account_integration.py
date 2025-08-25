# Copyright (c) 2025, Monika and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
import requests
import base64
import json

from cryptography.hazmat.primitives import serialization, hashes, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def decrypt_bank_response(encrypted_response: str, private_key_path: str) -> dict:
    print("Decryption Process Started")

    decoded_json = base64.b64decode(encrypted_response).decode("utf-8")
    print("Base64 Decoded JSON String", decoded_json)

    payload = json.loads(decoded_json)
    print("payload", payload)

    enc_key_b64 = payload["key"]
    print("enc_key_b64", enc_key_b64)
    iv_b64 = payload["iv"]
    print("iv_b64", iv_b64)
    data_b64 = payload["data"]
    print("data_b64", data_b64)

    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend(),
        )
    print("Loaded Private RSA Key")

    enc_key = base64.b64decode(enc_key_b64)
    print("kkkkkk", enc_key)
    aes_key = private_key.decrypt(
        enc_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    print("AES Key decrypted")

    iv = base64.b64decode(iv_b64)
    print("iv", iv)
    ciphertext = base64.b64decode(data_b64)
    print("cipertext", ciphertext)
    print("Decrypting AES-CBC")

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    print("cc",cipher)
    decryptor = cipher.decryptor()
    print("Decryptor created", decryptor)
    padded_plain = decryptor.update(ciphertext) + decryptor.finalize()
    print("Padded Plaintext:", padded_plain)

    unpadder = sym_padding.PKCS7(128).unpadder()
    print("Unpadder created", unpadder)
    plain = unpadder.update(padded_plain) + unpadder.finalize()
    print("Plaintext after unpadding:", plain)

    result = json.loads(plain.decode("utf-8"))
    print("Final Decrypted JSON:", result)
    print("Decryption Complete")
    return result


class BankAccountIntegration(Document):
    pass


@frappe.whitelist()
def send_account_bank(account_name, phone, address, email, account_type):
    url = "http://192.168.1.38:8000/api/method/bank_service.api.create_bank_account"

    with open("/home/monika/public_key.pem", "r") as f:
        public_key_pem = f.read()

    form_data = {
        "account_name": account_name,
        "phone": phone,
        "address": address,
        "email": email,
        "account_type": account_type,
        "client_public_key_file": public_key_pem,
    }
    print("Form Data:", form_data)

    try:
        res = requests.post(url, json=form_data)
        print("Response:", res)

        if res.status_code != 200:
            return {"message": f"Failed: {res.status_code} {res.text}"}

        response_json = res.json()
        print("Raw Response JSON:", response_json)

        message = response_json.get("message", {})

        if isinstance(message, dict) and "encrypted_response" in message:
            print("Encrypted Response Found")
            decrypted_message = decrypt_bank_response(
                message["encrypted_response"], "/home/monika/private_key.pem"
            )
            print("Decrypted:", decrypted_message)
            message = decrypted_message
        else:
            print("No encryption, using plain message")

        print("Message (final):", message)
        

        doc = frappe.new_doc("Bank Account Integration")
        doc.account_name = account_name
        doc.account_number = message.get("account_number")
        doc.account_type = account_type
        doc.bank_public_key=message.get("bank_public_key")
        doc.insert()
        #full_bank_name = message.get("erpnext_bank_account") 
        bank_name = message.get("erpnext_bank_account")   # result = "HDFC"
        if not frappe.db.exists("Bank", bank_name):
            bank_doc = frappe.new_doc("Bank")
            bank_doc.bank_name = bank_name
            bank_doc.insert()
            print(f"Created new Bank: {bank_name}")
        if not frappe.db.exists("Bank Account", {"bank_account_number": message.get("account_number")}):
            bank_account_doc = frappe.new_doc("Bank Account")
            bank_account_doc.account_name = account_name
            bank_account_doc.bank_account_no = message.get("account_number")
            bank_account_doc.account_type = account_type
            bank_account_doc.bank = bank_name
            bank_account_doc.is_company_account = 1
            bank_account_doc.company = frappe.db.get_value("Company", {}, "name", order_by="creation desc")
            print("hhhhhh",bank_account_doc.company)
            bank_account_doc.insert()
            print(f"Created new Bank Account: {message.get('account_number')}")
        else:
            print("Bank Account already exists, skipping creation.")

        doc=frappe.new_doc("Account")
        doc.account_name = account_name
        doc.account_number = message.get("account_number")
        company_doc = frappe.db.get_value("Company", {}, "name", order_by="creation desc")
        doc.company = company_doc.name
        
        #doc.company_abbr= company_doc.company_abbr
        doc.parent_account = "Bank Accounts - " + company_doc.company_abbr
        doc.insert()



        


        return {
            "message": "Details sent to bank company successfully!",
            "bank_response": message,
        }
    

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bank API Error")
        return {"message": "Error occurred"}


# transaction section - send encrypted transaction details to bank