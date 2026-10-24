import sqlite3
from pathlib import Path


# Get the V2 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database file
DATABASE_PATH = BASE_DIR / "banking.db"


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """
    connection = sqlite3.connect(DATABASE_PATH)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_tables():
    """
    Create all banking database tables.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # 1. CUSTOMERS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            customer_since TEXT NOT NULL,
            customer_status TEXT NOT NULL
        )
    """)

    # ---------------------------------------------------------
    # 2. ACCOUNTS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            account_number TEXT NOT NULL UNIQUE,
            account_type TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'INR',
            branch_id INTEGER,
            account_status TEXT NOT NULL,
            opened_date TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        )
    """)

    # ---------------------------------------------------------
    # 3. TRANSACTIONS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY,
            account_id INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            merchant TEXT,
            category TEXT,
            description TEXT,
            reference_number TEXT UNIQUE,
            transaction_status TEXT NOT NULL,

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        )
    """)

    # ---------------------------------------------------------
    # 4. SUPPORT TICKETS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            account_id INTEGER,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        )
    """)

    # ---------------------------------------------------------
    # 5. BENEFICIARIES
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS beneficiaries (
            beneficiary_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            beneficiary_name TEXT NOT NULL,
            beneficiary_account TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            ifsc_code TEXT NOT NULL,
            relationship TEXT,
            added_date TEXT NOT NULL,
            beneficiary_status TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        )
    """)

    # ---------------------------------------------------------
    # 6. LOANS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL,
            principal_amount REAL NOT NULL,
            outstanding_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            tenure_months INTEGER NOT NULL,
            emi_amount REAL NOT NULL,
            start_date TEXT NOT NULL,
            next_emi_date TEXT NOT NULL,
            loan_status TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        )
    """)

    # ---------------------------------------------------------
    # 7. CARDS
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            card_type TEXT NOT NULL,
            card_network TEXT NOT NULL,
            last_four_digits TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            card_status TEXT NOT NULL,
            daily_limit REAL NOT NULL,
            issued_date TEXT NOT NULL,

            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        )
    """)

    # ---------------------------------------------------------
    # 8. BRANCHES
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            branch_id INTEGER PRIMARY KEY,
            branch_code TEXT NOT NULL UNIQUE,
            branch_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            address TEXT NOT NULL,
            pincode TEXT NOT NULL,
            ifsc_code TEXT NOT NULL UNIQUE,
            contact_number TEXT NOT NULL,
            branch_status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("All banking tables created successfully.")