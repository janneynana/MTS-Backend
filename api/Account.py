"""
File to interact with the database.
"""

import string
import random
import psycopg2
from config import Config
from Database import *

# Function that creates an account in the database.
# The only fields that will be populated will be the email and the Access Code
# The access code will be made in this function.
# All other fields will be filled when the account is created by the admin


class Account:
    # base constructor
    def __init__(self, email, password, authCode, role):
        self.email = email
        self.password = password
        self.authCode = authCode
        self.role = role


    def set_role(self, role):
        self.role = role


    def initialize(self):
        connection = psycopg2.connect(
            host="ibf-mst-cs407.postgres.database.azure.com",
            database="postgres",
            user="cs407",
            password="IBF-MTS-pwd",
            port=5432,
            sslmode="require"
        )
        print("Connection established")
        return connection

    def initialize_account(self):
        self.authCode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        print(self.authCode)
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO account (email, password, \"authCode\", \"role\") VALUES (%s, %s, %s, %s);",
                       (str(self.email), '', str(self.authCode), 'admin'))
        connection.commit()
        cursor.close()
        connection.close()
        return [self.authCode, cursor.rowcount]

    """
    Function that verifies email and authCode prior to creating a full account
    """

    def verify_account(self):
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("SELECT email, \"authCode\" FROM account WHERE email='{0}' AND \"authCode\"='{1}';"
                       .format(self.email, self.authCode))
        print(cursor.rowcount)
        return cursor.rowcount


    def create_account(self):
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("Update account SET password = '{0}' WHERE email = '{1}' AND \"authCode\"='{2}';"
                       .format(self.password, self.email, self.authCode))
        print(cursor.rowcount)
        row = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return row

    """
    Function already exists checks database is email is already used. 
    Returns account, if found
    """

    def already_exists(self):
        print("Checking to see if account already exists")
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM account WHERE email='{0}';".format(self.email))
        rows = cursor.fetchall()
        print(rows)
        return rows

    def delete_account(self):
        print("Deleting account")
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM account where email='{0}';".format(self.email))
        rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return rows

    def edit_role(self, role):
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("UPDATE account SET role='{0}' WHERE email='{1}';".format(role, self.email))
        rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return rows

    def get_admins(self):
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM account WHERE role='root'")
        rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return rows

    def set_code(self, code):
        connection = self.initialize()
        cursor = connection.cursor()
        cursor.execute("UPDATE account SET \"authCode\"='{0}' WHERE id={1} AND email='{2}';".format(code, 0, "CODE"))
        rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return rows