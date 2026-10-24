import sys
from pathlib import Path
from datetime import date, timedelta
import random
import string

# ---------------------------------------------------------
# Make V2 project root available for imports
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from faker import Faker
from database.db import get_connection, create_tables


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

fake = Faker("en_IN")

random.seed(42)
Faker.seed(42)

NUM_CUSTOMERS = 50
NUM_BRANCHES = 15

MIN_ACCOUNTS = 1
MAX_ACCOUNTS = 2

MIN_TRANSACTIONS = 15
MAX_TRANSACTIONS = 30

MIN_BENEFICIARIES = 1
MAX_BENEFICIARIES = 2

NUM_LOANS = 40
NUM_CARDS = 75
NUM_TICKETS = 100


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def random_date(start_date, end_date):
    """Return a random date between two dates."""

    delta = end_date - start_date

    random_days = random.randint(0, delta.days)

    return start_date + timedelta(days=random_days)


def generate_account_number(existing_numbers):
    """Generate a unique 10-digit account number."""

    while True:
        number = str(random.randint(1000000000, 9999999999))

        if number not in existing_numbers:
            existing_numbers.add(number)
            return number


def generate_reference_number():
    """Generate a transaction reference number."""

    prefix = "TXN"

    random_part = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=12
        )
    )

    return prefix + random_part


def generate_ifsc(branch_code):
    """Generate a fictional IFSC code."""

    return f"VGBA000{branch_code:05d}"


# ---------------------------------------------------------
# Branch generation
# ---------------------------------------------------------

def generate_branches(connection):
    print("Generating branches...")

    cursor = connection.cursor()

    branches = []

    branch_locations = [
        ("Pune", "Maharashtra"),
        ("Mumbai", "Maharashtra"),
        ("Bangalore", "Karnataka"),
        ("Hyderabad", "Telangana"),
        ("Chennai", "Tamil Nadu"),
        ("Delhi", "Delhi"),
        ("Noida", "Uttar Pradesh"),
        ("Gurgaon", "Haryana"),
        ("Ahmedabad", "Gujarat"),
        ("Kolkata", "West Bengal"),
        ("Jaipur", "Rajasthan"),
        ("Indore", "Madhya Pradesh"),
        ("Nagpur", "Maharashtra"),
        ("Surat", "Gujarat"),
        ("Nashik", "Maharashtra"),
    ]

    for branch_id in range(1, NUM_BRANCHES + 1):

        city, state = branch_locations[branch_id - 1]

        branch_code = f"{branch_id:05d}"

        branch_name = f"VG Bank {city} Main Branch"

        address = fake.street_address()

        pincode = fake.postcode()

        ifsc_code = generate_ifsc(branch_id)

        contact_number = fake.numerify(
            text="9#########"
        )

        branch_status = random.choice(
            ["ACTIVE", "ACTIVE", "ACTIVE", "UNDER_MAINTENANCE"]
        )

        cursor.execute(
            """
            INSERT INTO branches (
                branch_id,
                branch_code,
                branch_name,
                city,
                state,
                address,
                pincode,
                ifsc_code,
                contact_number,
                branch_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                branch_id,
                branch_code,
                branch_name,
                city,
                state,
                address,
                pincode,
                ifsc_code,
                contact_number,
                branch_status,
            ),
        )

        branches.append(branch_id)

    return branches


# ---------------------------------------------------------
# Customer generation
# ---------------------------------------------------------

def generate_customers(connection):
    print("Generating customers...")

    cursor = connection.cursor()

    customers = []

    start_date = date(2018, 1, 1)
    end_date = date(2025, 12, 31)

    for customer_id in range(1, NUM_CUSTOMERS + 1):

        full_name = fake.name()

        email = f"customer{customer_id}@examplebank.com"

        phone = fake.numerify(
            text="9#########"
        )

        dob = fake.date_of_birth(
            minimum_age=21,
            maximum_age=65
        )

        address = fake.street_address()

        city = fake.city()

        state = fake.state()

        pincode = fake.postcode()

        customer_since = random_date(
            start_date,
            end_date
        )

        customer_status = random.choice(
            ["ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE"]
        )

        cursor.execute(
            """
            INSERT INTO customers (
                customer_id,
                full_name,
                email,
                phone,
                date_of_birth,
                address,
                city,
                state,
                pincode,
                customer_since,
                customer_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                full_name,
                email,
                phone,
                dob.isoformat(),
                address,
                city,
                state,
                pincode,
                customer_since.isoformat(),
                customer_status,
            ),
        )

        customers.append(customer_id)

    return customers


# ---------------------------------------------------------
# Account generation
# ---------------------------------------------------------

def generate_accounts(connection, customers, branches):
    print("Generating accounts...")

    cursor = connection.cursor()

    accounts = []

    existing_account_numbers = set()

    account_id = 1

    for customer_id in customers:

        number_of_accounts = random.randint(
            MIN_ACCOUNTS,
            MAX_ACCOUNTS
        )

        for _ in range(number_of_accounts):

            account_number = generate_account_number(
                existing_account_numbers
            )

            account_type = random.choice(
                ["SAVINGS", "SAVINGS", "CURRENT"]
            )

            balance = round(
                random.uniform(5000, 500000),
                2
            )

            currency = "INR"

            branch_id = random.choice(branches)

            account_status = random.choice(
                ["ACTIVE", "ACTIVE", "ACTIVE", "FROZEN", "CLOSED"]
            )

            opened_date = random_date(
                date(2018, 1, 1),
                date(2025, 12, 31)
            )

            cursor.execute(
                """
                INSERT INTO accounts (
                    account_id,
                    customer_id,
                    account_number,
                    account_type,
                    balance,
                    currency,
                    branch_id,
                    account_status,
                    opened_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id,
                    customer_id,
                    account_number,
                    account_type,
                    balance,
                    currency,
                    branch_id,
                    account_status,
                    opened_date.isoformat(),
                ),
            )

            accounts.append({
                "account_id": account_id,
                "customer_id": customer_id,
                "account_number": account_number,
                "balance": balance,
            })

            account_id += 1

    return accounts


# ---------------------------------------------------------
# Transaction generation
# ---------------------------------------------------------

def generate_transactions(connection, accounts):
    print("Generating transactions...")

    cursor = connection.cursor()

    transaction_id = 1

    merchants = [
        "Amazon",
        "Flipkart",
        "Swiggy",
        "Zomato",
        "Uber",
        "Ola",
        "Reliance Retail",
        "DMart",
        "Big Bazaar",
        "Myntra",
        "BookMyShow",
        "Apollo Pharmacy",
        "Airtel",
        "Jio",
        "Netflix",
        "Electricity Board",
        "Indian Oil",
        "HP Petrol Pump",
        "IRCTC",
        "MakeMyTrip",
        "Air India",
        "IndiGo",
        "Local Grocery Store",
        "Online Transfer",
        "Salary Credit",
    ]

    debit_categories = [
        "Shopping",
        "Food",
        "Transportation",
        "Entertainment",
        "Healthcare",
        "Utilities",
        "Travel",
        "Groceries",
        "Fuel",
        "Rent",
    ]

    credit_sources = [
        ("Salary Credit", "Salary"),
        ("Refund", "Refund"),
        ("Bank Transfer", "Transfer"),
        ("Interest Credit", "Interest"),
        ("Cash Deposit", "Cash Deposit"),
    ]

    for account in accounts:

        number_of_transactions = random.randint(
            MIN_TRANSACTIONS,
            MAX_TRANSACTIONS
        )

        for _ in range(number_of_transactions):

            transaction_type = random.choice(
                ["DEBIT", "DEBIT", "DEBIT", "CREDIT"]
            )

            if transaction_type == "CREDIT":

                merchant, category = random.choice(
                    credit_sources
                )

                amount = round(
                    random.uniform(5000, 100000),
                    2
                )

                description = f"Credit received from {merchant}"

            else:

                merchant = random.choice(merchants[:-1])

                category = random.choice(
                    debit_categories
                )

                amount = round(
                    random.uniform(500, 50000),
                    2
                )

                description = f"Payment made to {merchant}"


            transaction_date = random_date(
                date(2025, 1, 1),
                date(2025, 9, 15)
            )

            reference_number = generate_reference_number()

            transaction_status = random.choice(
                ["SUCCESS", "SUCCESS", "SUCCESS", "PENDING", "FAILED"]
            )

            cursor.execute(
                """
                INSERT INTO transactions (
                    transaction_id,
                    account_id,
                    transaction_date,
                    transaction_type,
                    amount,
                    merchant,
                    category,
                    description,
                    reference_number,
                    transaction_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    account["account_id"],
                    transaction_date.isoformat(),
                    transaction_type,
                    amount,
                    merchant,
                    category,
                    description,
                    reference_number,
                    transaction_status,
                ),
            )

            transaction_id += 1


# ---------------------------------------------------------
# Beneficiary generation
# ---------------------------------------------------------

def generate_beneficiaries(connection, customers):
    print("Generating beneficiaries...")

    cursor = connection.cursor()

    beneficiary_id = 1

    banks = [
        "VG Bank",
        "State Bank",
        "National Bank",
        "Union Bank",
        "Horizon Bank",
    ]

    relationships = [
        "Family",
        "Friend",
        "Business",
        "Self",
        "Other",
    ]

    for customer_id in customers:

        number_of_beneficiaries = random.randint(
            MIN_BENEFICIARIES,
            MAX_BENEFICIARIES
        )

        for _ in range(number_of_beneficiaries):

            beneficiary_name = fake.name()

            beneficiary_account = str(
                random.randint(
                    1000000000,
                    9999999999
                )
            )

            bank_name = random.choice(banks)

            ifsc_code = (
                "VGBA" +
                "".join(
                    random.choices(
                        string.ascii_uppercase +
                        string.digits,
                        k=7
                    )
                )
            )

            relationship = random.choice(
                relationships
            )

            added_date = random_date(
                date(2020, 1, 1),
                date(2025, 9, 15)
            )

            beneficiary_status = random.choice(
                ["ACTIVE", "ACTIVE", "BLOCKED"]
            )

            cursor.execute(
                """
                INSERT INTO beneficiaries (
                    beneficiary_id,
                    customer_id,
                    beneficiary_name,
                    beneficiary_account,
                    bank_name,
                    ifsc_code,
                    relationship,
                    added_date,
                    beneficiary_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    beneficiary_id,
                    customer_id,
                    beneficiary_name,
                    beneficiary_account,
                    bank_name,
                    ifsc_code,
                    relationship,
                    added_date.isoformat(),
                    beneficiary_status,
                ),
            )

            beneficiary_id += 1


# ---------------------------------------------------------
# Loan generation
# ---------------------------------------------------------

def generate_loans(connection, customers):
    print("Generating loans...")

    cursor = connection.cursor()

    loan_types = [
        "HOME",
        "PERSONAL",
        "CAR",
        "EDUCATION",
    ]

    for loan_id in range(1, NUM_LOANS + 1):

        customer_id = random.choice(customers)

        loan_type = random.choice(loan_types)

        principal_amount = round(
            random.choice(
                [
                    200000,
                    500000,
                    750000,
                    1000000,
                    1500000,
                    2500000,
                    5000000,
                ]
            ),
            2
        )

        outstanding_percentage = random.uniform(
            0.1,
            0.9
        )

        outstanding_amount = round(
            principal_amount *
            outstanding_percentage,
            2
        )

        interest_rate = round(
            random.uniform(7.0, 14.5),
            2
        )

        tenure_months = random.choice(
            [12, 24, 36, 48, 60, 84, 120, 180]
        )

        emi_amount = round(
            (
                principal_amount /
                tenure_months
            ) *
            (
                1 +
                interest_rate / 100
            ),
            2
        )

        start_date = random_date(
            date(2020, 1, 1),
            date(2025, 1, 1)
        )

        next_emi_date = start_date + timedelta(
            days=random.randint(1, 30)
        )

        loan_status = random.choice(
            ["ACTIVE", "ACTIVE", "CLOSED", "OVERDUE"]
        )

        cursor.execute(
            """
            INSERT INTO loans (
                loan_id,
                customer_id,
                loan_type,
                principal_amount,
                outstanding_amount,
                interest_rate,
                tenure_months,
                emi_amount,
                start_date,
                next_emi_date,
                loan_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                loan_id,
                customer_id,
                loan_type,
                principal_amount,
                outstanding_amount,
                interest_rate,
                tenure_months,
                emi_amount,
                start_date.isoformat(),
                next_emi_date.isoformat(),
                loan_status,
            ),
        )


# ---------------------------------------------------------
# Card generation
# ---------------------------------------------------------

def generate_cards(connection, customers, accounts):
    print("Generating cards...")

    cursor = connection.cursor()

    card_id = 1

    card_types = [
        "DEBIT",
        "DEBIT",
        "CREDIT",
    ]

    networks = [
        "VISA",
        "MASTERCARD",
        "RUPAY",
    ]

    for _ in range(NUM_CARDS):

        account = random.choice(accounts)

        customer_id = account["customer_id"]

        card_type = random.choice(card_types)

        card_network = random.choice(networks)

        last_four_digits = str(
            random.randint(1000, 9999)
        )

        expiry_date = (
            date.today() +
            timedelta(
                days=random.randint(
                    180,
                    1800
                )
            )
        )

        card_status = random.choice(
            ["ACTIVE", "ACTIVE", "BLOCKED", "EXPIRED"]
        )

        daily_limit = random.choice(
            [
                25000,
                50000,
                75000,
                100000,
                200000,
            ]
        )

        issued_date = date.today() - timedelta(
            days=random.randint(
                30,
                1500
            )
        )

        cursor.execute(
            """
            INSERT INTO cards (
                card_id,
                customer_id,
                account_id,
                card_type,
                card_network,
                last_four_digits,
                expiry_date,
                card_status,
                daily_limit,
                issued_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card_id,
                customer_id,
                account["account_id"],
                card_type,
                card_network,
                last_four_digits,
                expiry_date.isoformat(),
                card_status,
                daily_limit,
                issued_date.isoformat(),
            ),
        )

        card_id += 1


# ---------------------------------------------------------
# Support ticket generation
# ---------------------------------------------------------

def generate_support_tickets(connection, customers, accounts):
    print("Generating support tickets...")

    cursor = connection.cursor()

    subjects = [
        "Unrecognized transaction",
        "Card payment issue",
        "ATM withdrawal issue",
        "Account balance discrepancy",
        "Unable to transfer money",
        "Beneficiary issue",
        "Loan EMI issue",
        "Credit card payment issue",
        "Account access problem",
        "Refund not received",
        "Transaction failed",
        "Card blocked",
    ]

    categories = [
        "TRANSACTION",
        "CARD",
        "ACCOUNT",
        "TRANSFER",
        "LOAN",
        "REFUND",
        "SECURITY",
    ]

    priorities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    statuses = [
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED",
    ]

    for ticket_id in range(1, NUM_TICKETS + 1):

        customer_id = random.choice(customers)

        customer_accounts = [
            account
            for account in accounts
            if account["customer_id"] == customer_id
        ]

        account = random.choice(
            customer_accounts
        )

        subject = random.choice(subjects)

        description = (
            f"Customer reported an issue related to "
            f"{subject.lower()}. "
            f"Please investigate and provide an update."
        )

        category = random.choice(categories)

        priority = random.choice(priorities)

        status = random.choice(statuses)

        created_at = random_date(
            date(2025, 1, 1),
            date(2025, 9, 15)
        )

        updated_at = created_at + timedelta(
            days=random.randint(0, 10)
        )

        cursor.execute(
            """
            INSERT INTO support_tickets (
                ticket_id,
                customer_id,
                account_id,
                subject,
                description,
                category,
                priority,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                customer_id,
                account["account_id"],
                subject,
                description,
                category,
                priority,
                status,
                created_at.isoformat(),
                updated_at.isoformat(),
            ),
        )


# ---------------------------------------------------------
# Database validation
# ---------------------------------------------------------

def validate_database(connection):
    print("\nValidating database...")
    print("-" * 50)

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

    for table in tables:

        result = connection.execute(
            f"SELECT COUNT(*) AS count FROM {table}"
        ).fetchone()

        print(
            f"{table:20} : {result['count']}"
        )

    print("-" * 50)

    # Check relationships
    orphan_accounts = connection.execute("""
        SELECT COUNT(*) AS count
        FROM accounts a
        LEFT JOIN customers c
            ON a.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """).fetchone()["count"]

    orphan_transactions = connection.execute("""
        SELECT COUNT(*) AS count
        FROM transactions t
        LEFT JOIN accounts a
            ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
    """).fetchone()["count"]

    print(
        f"Orphan accounts     : {orphan_accounts}"
    )

    print(
        f"Orphan transactions  : {orphan_transactions}"
    )

    if (
        orphan_accounts == 0
        and orphan_transactions == 0
    ):
        print("\nDatabase validation PASSED.")
    else:
        print("\nDatabase validation FAILED.")


# ---------------------------------------------------------
# Main seeding function
# ---------------------------------------------------------

def seed_database():

    print("=" * 60)
    print("VG BANK - MOCK DATABASE SEEDING")
    print("=" * 60)

    # Make sure tables exist
    create_tables()

    connection = get_connection()

    try:

        # Clear existing data
        print("\nClearing existing data...")

        connection.execute(
            "DELETE FROM transactions"
        )

        connection.execute(
            "DELETE FROM support_tickets"
        )

        connection.execute(
            "DELETE FROM cards"
        )

        connection.execute(
            "DELETE FROM loans"
        )

        connection.execute(
            "DELETE FROM beneficiaries"
        )

        connection.execute(
            "DELETE FROM accounts"
        )

        connection.execute(
            "DELETE FROM customers"
        )

        connection.execute(
            "DELETE FROM branches"
        )

        connection.commit()

        # Generate data
        branches = generate_branches(
            connection
        )

        customers = generate_customers(
            connection
        )

        accounts = generate_accounts(
            connection,
            customers,
            branches
        )

        generate_transactions(
            connection,
            accounts
        )

        generate_beneficiaries(
            connection,
            customers
        )

        generate_loans(
            connection,
            customers
        )

        generate_cards(
            connection,
            customers,
            accounts
        )

        generate_support_tickets(
            connection,
            customers,
            accounts
        )

        connection.commit()

        # Validate
        validate_database(
            connection
        )

        print("\n" + "=" * 60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as error:

        connection.rollback()

        print("\nDATABASE SEEDING FAILED")
        print(f"Error: {error}")

        raise

    finally:

        connection.close()


if __name__ == "__main__":
    seed_database()