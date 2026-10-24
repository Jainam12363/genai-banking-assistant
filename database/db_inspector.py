import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_connection


def show_database_summary():

    connection = get_connection()

    tables = [
        "customers",
        "accounts",
        "transactions",
        "support_tickets",
        "beneficiaries",
        "loans",
        "cards",
        "branches",
    ]

    print("\nVG BANK DATABASE SUMMARY")
    print("=" * 40)

    for table in tables:

        result = connection.execute(
            f"SELECT COUNT(*) AS count FROM {table}"
        ).fetchone()

        print(f"{table:20} : {result['count']}")

    print("\nSAMPLE CUSTOMER")
    print("=" * 40)

    customer = connection.execute("""
        SELECT *
        FROM customers
        LIMIT 1
    """).fetchone()

    for key in customer.keys():
        print(f"{key}: {customer[key]}")

    print("\nSAMPLE ACCOUNT")
    print("=" * 40)

    account = connection.execute("""
        SELECT *
        FROM accounts
        LIMIT 1
    """).fetchone()

    for key in account.keys():
        print(f"{key}: {account[key]}")

    print("\nSAMPLE TRANSACTION")
    print("=" * 40)

    transaction = connection.execute("""
        SELECT *
        FROM transactions
        LIMIT 1
    """).fetchone()

    for key in transaction.keys():
        print(f"{key}: {transaction[key]}")

    connection.close()


if __name__ == "__main__":
    show_database_summary()