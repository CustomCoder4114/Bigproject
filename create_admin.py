"""
Create (or promote) an admin account for the eSchool app.

Usage:
    python create_admin.py

Run this from the same folder as app.py / users.db. It will:
  - Import init_db() from app.py first, so the users table (and the
    role column) definitely exist, even on a totally fresh database.
  - Prompt for first name, last name, email, and password.
  - If an account with that email already exists, promote it to
    'admin' (and update its password to what you just entered).
  - Otherwise, create a brand new account with role='admin'.

Note on passwords: app.py currently compares passwords as plain text
(`WHERE email = ? AND password = ?` in /Login), so this script stores
the password the same way, in plain text, to stay consistent with how
login already works. If you want real password hashing later, you'd
switch both /Login and /register (and this script) over to
werkzeug.security's generate_password_hash / check_password_hash at
the same time - mixing plain text and hashed passwords in one table
would break login for whichever accounts don't match the new format.
"""

import sqlite3

from backen import init_db  # ensures the users table + role column exist


def create_admin():
    init_db()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    print("=== Create / Promote Admin Account ===")
    firstname = input("First name: ").strip()
    lastname = input("Last name: ").strip()
    email = input("Email: ").strip()
    print("(Password will be visible as you type - it's stored in plain text either way, same as /Login.)")
    password = input("Password: ").strip()
    confirm = input("Confirm password: ").strip()

    if not (firstname and lastname and email and password):
        print("All fields are required. Nothing was created.")
        conn.close()
        return

    if password != confirm:
        print("Passwords did not match. Nothing was created.")
        conn.close()
        return

    cursor.execute("SELECT id, role FROM users WHERE email = ?", (email,))
    existing = cursor.fetchone()

    if existing:
        user_id, current_role = existing
        cursor.execute(
            "UPDATE users SET role = 'admin', password = ?, firstname = ?, lastname = ? WHERE id = ?",
            (password, firstname, lastname, user_id)
        )
        conn.commit()
        if current_role == 'admin':
            print(f"'{email}' was already an admin. Password/name updated.")
        else:
            print(f"Existing account '{email}' (was '{current_role}') promoted to admin.")
    else:
        cursor.execute('''
            INSERT INTO users (firstname, lastname, email, password, role)
            VALUES (?, ?, ?, ?, 'admin')
        ''', (firstname, lastname, email, password))
        conn.commit()
        print(f"Admin account created for '{email}'.")

    conn.close()


if __name__ == '__main__':
    create_admin()