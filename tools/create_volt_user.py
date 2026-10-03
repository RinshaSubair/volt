#!/usr/bin/env python3
"""
Volt EEE Mastery Platform - Admin User Provisioning Tool
-------------------------------------------------------
Since self-registration is strictly disabled on the client,
administrators use this tool to provision authorized student accounts.
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

FIREBASE_API_KEY = "AIzaSyAuQJeEePogtOzcKQGLi2yR_N1WrHdv8To"
SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
UPDATE_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FIREBASE_API_KEY}"

def create_student_user(email: str, password: str, display_name: str = None):
    print(f"[*] Provisioning account for: {email}...")
    
    signup_payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    }).encode("utf-8")
    
    req = urllib.request.Request(
        SIGNUP_URL,
        data=signup_payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            local_id = data.get("localId")
            id_token = data.get("idToken")
            print(f"[+] Account created successfully! UID: {local_id}")
            
            if display_name and id_token:
                update_payload = json.dumps({
                    "idToken": id_token,
                    "displayName": display_name,
                    "returnSecureToken": False
                }).encode("utf-8")
                up_req = urllib.request.Request(
                    UPDATE_URL,
                    data=update_payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(up_req) as up_resp:
                    print(f"[+] Display name set to: {display_name}")
            
            print(f"[✓] Student {email} is now authorized to log in to Volt.")
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body
            
        if "EMAIL_EXISTS" in msg:
            print(f"[-] Error: An account with email '{email}' already exists.")
        elif "WEAK_PASSWORD" in msg:
            print("[-] Error: Password is too weak. Must be at least 6 characters.")
        elif "INVALID_EMAIL" in msg:
            print(f"[-] Error: '{email}' is not a valid email address.")
        else:
            print(f"[-] Firebase error: {msg}")
        return False
    except Exception as e:
        print(f"[-] Network or unexpected error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Volt Admin - Create Authorized Student Account")
    parser.add_argument("--email", "-e", required=True, help="Student email address")
    parser.add_argument("--password", "-p", required=True, help="Initial password (min 6 characters)")
    parser.add_argument("--name", "-n", default=None, help="Student display name (optional)")
    
    args = parser.parse_args()
    success = create_student_user(args.email, args.password, args.name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
