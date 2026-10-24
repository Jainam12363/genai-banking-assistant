from database.db import get_connection
from datetime import datetime


def get_database_connection():
    """
    Return a connection to the banking database.
    """
    return get_connection()

def get_account_by_number(account_number):
    """
    Retrieve account information using the account number.
    """

    connection = get_database_connection()

    account = connection.execute(
        """
        SELECT
            account_id,
            customer_id,
            account_number,
            account_type,
            balance,
            currency,
            branch_id,
            account_status,
            opened_date
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,)
    ).fetchone()

    connection.close()

    return account

def get_transactions_by_account(
    account_number,
    start_date=None,
    end_date=None
):
    """
    Retrieve transactions for an account.

    Optional start_date and end_date can be used
    to filter transactions by date.
    """

    connection = get_database_connection()

    query = """
        SELECT
            t.transaction_id,
            t.account_id,
            a.account_number,
            t.transaction_date,
            t.transaction_type,
            t.amount,
            t.merchant,
            t.category,
            t.description,
            t.reference_number,
            t.transaction_status
        FROM transactions t
        JOIN accounts a
            ON t.account_id = a.account_id
        WHERE a.account_number = ?
    """

    parameters = [account_number]

    if start_date:
        query += " AND t.transaction_date >= ?"
        parameters.append(start_date)

    if end_date:
        query += " AND t.transaction_date <= ?"
        parameters.append(end_date)

    query += " ORDER BY t.transaction_date DESC"

    transactions = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return transactions

def get_customer_by_id(customer_id):
    """
    Retrieve customer information using customer ID.
    """

    connection = get_database_connection()

    customer = connection.execute(
        """
        SELECT
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
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)
    ).fetchone()

    connection.close()

    return customer


def get_tickets_by_customer(customer_id):
    """
    Retrieve support tickets for a customer.
    """

    connection = get_database_connection()

    tickets = connection.execute(
        """
        SELECT
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
        FROM support_tickets
        WHERE customer_id = ?
        ORDER BY created_at DESC
        """,
        (customer_id,)
    ).fetchall()

    connection.close()

    return tickets


def get_loans_by_customer(customer_id):
    """
    Retrieve loans for a customer.
    """

    connection = get_database_connection()

    loans = connection.execute(
        """
        SELECT
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
        FROM loans
        WHERE customer_id = ?
        ORDER BY start_date DESC
        """,
        (customer_id,)
    ).fetchall()

    connection.close()

    return loans


def get_cards_by_customer(customer_id):
    """
    Retrieve cards for a customer.
    """

    connection = get_database_connection()

    cards = connection.execute(
        """
        SELECT
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
        FROM cards
        WHERE customer_id = ?
        ORDER BY issued_date DESC
        """,
        (customer_id,)
    ).fetchall()

    connection.close()

    return cards

def get_beneficiaries_by_customer(customer_id):
    """
    Retrieve beneficiaries for a customer.
    """

    connection = get_database_connection()

    beneficiaries = connection.execute(
        """
        SELECT
            beneficiary_id,
            customer_id,
            beneficiary_name,
            beneficiary_account,
            bank_name,
            ifsc_code,
            relationship,
            added_date,
            beneficiary_status
        FROM beneficiaries
        WHERE customer_id = ?
        ORDER BY added_date DESC
        """,
        (customer_id,)
    ).fetchall()

    connection.close()

    return beneficiaries


def get_all_branches():
    """
    Retrieve all active banking branches.
    """

    connection = get_database_connection()

    branches = connection.execute(
        """
        SELECT
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
        FROM branches
        WHERE branch_status = 'ACTIVE'
        ORDER BY city, branch_name
        """
    ).fetchall()

    connection.close()

    return branches



def freeze_account(account_number):
    """
    Freeze an active account.
    Only ACTIVE accounts can be frozen.
    """

    connection = get_database_connection()

    account = connection.execute(
        """
        SELECT
            account_id,
            account_number,
            account_status
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,)
    ).fetchone()

    if account is None:
        connection.close()
        raise ValueError("Account not found.")

    if account["account_status"] != "ACTIVE":
        connection.close()
        raise ValueError(
            f"Account cannot be frozen because its current status "
            f"is {account['account_status']}."
        )

    connection.execute(
        """
        UPDATE accounts
        SET account_status = 'FROZEN'
        WHERE account_number = ?
          AND account_status = 'ACTIVE'
        """,
        (account_number,)
    )

    connection.commit()

    updated_account = connection.execute(
        """
        SELECT
            account_id,
            customer_id,
            account_number,
            account_type,
            balance,
            currency,
            branch_id,
            account_status,
            opened_date
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,)
    ).fetchone()

    connection.close()

    return updated_account


def unfreeze_account(account_number):
    """
    Unfreeze a frozen account.
    Only FROZEN accounts can be unfrozen.
    """

    connection = get_database_connection()

    account = connection.execute(
        """
        SELECT
            account_id,
            account_number,
            account_status
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,)
    ).fetchone()

    if account is None:
        connection.close()
        raise ValueError("Account not found.")

    if account["account_status"] != "FROZEN":
        connection.close()
        raise ValueError(
            f"Account cannot be unfrozen because its current status "
            f"is {account['account_status']}."
        )

    connection.execute(
        """
        UPDATE accounts
        SET account_status = 'ACTIVE'
        WHERE account_number = ?
          AND account_status = 'FROZEN'
        """,
        (account_number,)
    )

    connection.commit()

    updated_account = connection.execute(
        """
        SELECT
            account_id,
            customer_id,
            account_number,
            account_type,
            balance,
            currency,
            branch_id,
            account_status,
            opened_date
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,)
    ).fetchone()

    connection.close()

    return updated_account


def update_customer_phone(customer_id, phone):
    """
    Update the phone number of an existing customer.
    """

    connection = get_database_connection()

    customer = connection.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)
    ).fetchone()

    if customer is None:
        connection.close()
        raise ValueError("Customer not found.")

    if not phone or not str(phone).strip():
        connection.close()
        raise ValueError("Phone number cannot be empty.")

    connection.execute(
        """
        UPDATE customers
        SET phone = ?
        WHERE customer_id = ?
        """,
        (str(phone).strip(), customer_id)
    )

    connection.commit()

    updated_customer = connection.execute(
        """
        SELECT
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
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)
    ).fetchone()

    connection.close()

    return updated_customer


def update_customer_email(customer_id, email):
    """
    Update the email address of an existing customer.
    """

    connection = get_database_connection()

    customer = connection.execute(
        """
        SELECT customer_id
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)
    ).fetchone()

    if customer is None:
        connection.close()
        raise ValueError("Customer not found.")

    if not email or not str(email).strip():
        connection.close()
        raise ValueError("Email address cannot be empty.")

    try:
        connection.execute(
            """
            UPDATE customers
            SET email = ?
            WHERE customer_id = ?
            """,
            (str(email).strip(), customer_id)
        )

        connection.commit()

    except Exception:
        connection.rollback()
        connection.close()
        raise

    updated_customer = connection.execute(
        """
        SELECT
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
        FROM customers
        WHERE customer_id = ?
        """,
        (customer_id,)
    ).fetchone()

    connection.close()

    return updated_customer


def block_card(card_id):
    """
    Block an active card.
    Only ACTIVE cards can be blocked.
    """

    connection = get_database_connection()

    card = connection.execute(
        """
        SELECT
            card_id,
            customer_id,
            account_id,
            last_four_digits,
            card_status
        FROM cards
        WHERE card_id = ?
        """,
        (card_id,)
    ).fetchone()

    if card is None:
        connection.close()
        raise ValueError("Card not found.")

    if card["card_status"] != "ACTIVE":
        connection.close()
        raise ValueError(
            f"Card cannot be blocked because its current status "
            f"is {card['card_status']}."
        )

    connection.execute(
        """
        UPDATE cards
        SET card_status = 'BLOCKED'
        WHERE card_id = ?
          AND card_status = 'ACTIVE'
        """,
        (card_id,)
    )

    connection.commit()

    updated_card = connection.execute(
        """
        SELECT
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
        FROM cards
        WHERE card_id = ?
        """,
        (card_id,)
    ).fetchone()

    connection.close()

    return updated_card


def unblock_card(card_id):
    """
    Unblock a blocked card.
    Only BLOCKED cards can be unblocked.
    """

    connection = get_database_connection()

    card = connection.execute(
        """
        SELECT
            card_id,
            customer_id,
            account_id,
            last_four_digits,
            card_status
        FROM cards
        WHERE card_id = ?
        """,
        (card_id,)
    ).fetchone()

    if card is None:
        connection.close()
        raise ValueError("Card not found.")

    if card["card_status"] != "BLOCKED":
        connection.close()
        raise ValueError(
            f"Card cannot be unblocked because its current status "
            f"is {card['card_status']}."
        )

    connection.execute(
        """
        UPDATE cards
        SET card_status = 'ACTIVE'
        WHERE card_id = ?
          AND card_status = 'BLOCKED'
        """,
        (card_id,)
    )

    connection.commit()

    updated_card = connection.execute(
        """
        SELECT
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
        FROM cards
        WHERE card_id = ?
        """,
        (card_id,)
    ).fetchone()

    connection.close()

    return updated_card



def create_support_ticket(
    customer_id,
    account_id,
    subject,
    description,
    category,
    priority
):
    """
    Create a new support ticket for a customer.
    """

    connection = get_database_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = connection.execute(
        """
        INSERT INTO support_tickets (
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            account_id,
            subject,
            description,
            category,
            priority,
            "OPEN",
            now,
            now
        )
    )

    connection.commit()

    ticket_id = cursor.lastrowid

    connection.close()

    return ticket_id


def update_support_ticket(
    ticket_id,
    status=None,
    priority=None,
    subject=None,
    description=None
):
    """
    Update controlled fields of an existing support ticket.
    """

    allowed_statuses = {
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
        "CLOSED"
    }

    allowed_priorities = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    connection = get_database_connection()

    ticket = connection.execute(
        """
        SELECT
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
        FROM support_tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    ).fetchone()

    if ticket is None:
        connection.close()
        raise ValueError("Support ticket not found.")

    if status is not None:
        status = str(status).strip().upper()

        if status not in allowed_statuses:
            connection.close()
            raise ValueError(
                f"Invalid ticket status: {status}."
            )

    if priority is not None:
        priority = str(priority).strip().upper()

        if priority not in allowed_priorities:
            connection.close()
            raise ValueError(
                f"Invalid ticket priority: {priority}."
            )

    updates = []
    parameters = []

    if status is not None:
        updates.append("status = ?")
        parameters.append(status)

    if priority is not None:
        updates.append("priority = ?")
        parameters.append(priority)

    if subject is not None:
        subject = str(subject).strip()

        if not subject:
            connection.close()
            raise ValueError("Subject cannot be empty.")

        updates.append("subject = ?")
        parameters.append(subject)

    if description is not None:
        description = str(description).strip()

        if not description:
            connection.close()
            raise ValueError("Description cannot be empty.")

        updates.append("description = ?")
        parameters.append(description)

    if not updates:
        connection.close()
        raise ValueError("At least one field must be provided for update.")

    updates.append("updated_at = ?")
    parameters.append(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    parameters.append(ticket_id)

    try:
        connection.execute(
            f"""
            UPDATE support_tickets
            SET {", ".join(updates)}
            WHERE ticket_id = ?
            """,
            parameters
        )

        connection.commit()

    except Exception:
        connection.rollback()
        connection.close()
        raise

    updated_ticket = connection.execute(
        """
        SELECT
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
        FROM support_tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    ).fetchone()

    connection.close()

    return updated_ticket