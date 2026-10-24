from io import BytesIO
from urllib.parse import urlparse
import sys

import requests

from mcp.server import MCPServer

from ddgs import DDGS

from official_sources import OFFICIAL_SOURCES
from pypdf import PdfReader

FASTAPI_URL = "http://127.0.0.1:8000"

MAX_RESULTS = 3



mcp = MCPServer("Banking MCP Server")


# ============================================================
# ACCOUNT
# ============================================================

@mcp.tool()
def get_account(account_number: str) -> dict:
    """
    Retrieve account details using an account number.
    """

    response = requests.get(
        f"{FASTAPI_URL}/accounts/{account_number}",
        timeout=30
    )

    if response.status_code == 404:
        return {"error": "Account not found."}

    response.raise_for_status()

    return response.json()


# ============================================================
# TRANSACTIONS
# ============================================================

@mcp.tool()
def get_transactions(account_number: str) -> dict:
    """
    Retrieve transactions for an account.
    """

    response = requests.get(
        f"{FASTAPI_URL}/accounts/{account_number}/transactions",
        timeout=30
    )

    if response.status_code == 404:
        return {"error": "Account not found."}

    response.raise_for_status()

    return response.json()


# ============================================================
# CUSTOMER
# ============================================================

@mcp.tool()
def get_customer(account_number: str) -> dict:
    """
    Retrieve customer information associated with an account.
    """

    account_response = requests.get(
        f"{FASTAPI_URL}/accounts/{account_number}",
        timeout=30
    )

    if account_response.status_code == 404:
        return {"error": "Account not found."}

    account_response.raise_for_status()

    account = account_response.json()

    customer_id = account.get("customer_id")

    if customer_id is None:
        return {
            "error": (
                "Customer ID could not be determined "
                "from the account."
            )
        }

    customer_response = requests.get(
        f"{FASTAPI_URL}/customers/{customer_id}",
        timeout=30
    )

    if customer_response.status_code == 404:
        return {"error": "Customer not found."}

    customer_response.raise_for_status()

    return customer_response.json()


# ============================================================
# SUPPORT TICKETS
# ============================================================

@mcp.tool()
def get_support_tickets(customer_id: int) -> dict:
    """
    Retrieve support tickets for a customer.

    Use this tool when the user asks about complaints,
    support tickets, complaint status, or previous issues.
    """

    response = requests.get(
        f"{FASTAPI_URL}/customers/{customer_id}/tickets",
        timeout=30
    )

    if response.status_code == 404:
        return {"error": "Customer not found."}

    response.raise_for_status()

    return response.json()


# ============================================================
# CALCULATOR
# ============================================================

@mcp.tool()
def calculate_banking(
    calculation_type: str,
    principal: float = 0,
    annual_rate: float = 0,
    tenure_months: int = 0,
    value: float = 0,
    total: float = 0,
    value1: float = 0,
    value2: float = 0
) -> dict:
    """
    Perform common banking and financial calculations.

    Supported calculation types:
    - emi
    - simple_interest
    - compound_interest
    - percentage
    - percentage_difference
    """

    calculation_type = (
        calculation_type
        .lower()
        .strip()
    )

    if calculation_type == "emi":

        if principal <= 0:
            raise ValueError(
                "Principal must be greater than zero."
            )

        if annual_rate < 0:
            raise ValueError(
                "Annual interest rate cannot be negative."
            )

        if tenure_months <= 0:
            raise ValueError(
                "Tenure must be greater than zero."
            )

        monthly_rate = (
            annual_rate / 12 / 100
        )

        if monthly_rate == 0:

            emi = principal / tenure_months

        else:

            emi = (
                principal
                * monthly_rate
                * (1 + monthly_rate) ** tenure_months
                / (
                    (1 + monthly_rate)
                    ** tenure_months
                    - 1
                )
            )

        total_payment = (
            emi * tenure_months
        )

        total_interest = (
            total_payment - principal
        )

        return {
            "calculation_type": "emi",
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
            "monthly_emi": round(emi, 2),
            "total_payment": round(
                total_payment,
                2
            ),
            "total_interest": round(
                total_interest,
                2
            )
        }

    elif calculation_type == "simple_interest":

        if principal < 0:
            raise ValueError(
                "Principal cannot be negative."
            )

        if annual_rate < 0:
            raise ValueError(
                "Annual interest rate cannot be negative."
            )

        if tenure_months < 0:
            raise ValueError(
                "Tenure cannot be negative."
            )

        years = tenure_months / 12

        interest = (
            principal
            * annual_rate
            * years
            / 100
        )

        total_amount = (
            principal + interest
        )

        return {
            "calculation_type": "simple_interest",
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
            "interest": round(
                interest,
                2
            ),
            "total_amount": round(
                total_amount,
                2
            )
        }

    elif calculation_type == "compound_interest":

        if principal < 0:
            raise ValueError(
                "Principal cannot be negative."
            )

        if annual_rate < 0:
            raise ValueError(
                "Annual interest rate cannot be negative."
            )

        if tenure_months < 0:
            raise ValueError(
                "Tenure cannot be negative."
            )

        years = tenure_months / 12

        amount = (
            principal
            * (
                1 + annual_rate / 100
            ) ** years
        )

        interest = (
            amount - principal
        )

        return {
            "calculation_type": "compound_interest",
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
            "interest": round(
                interest,
                2
            ),
            "total_amount": round(
                amount,
                2
            )
        }

    elif calculation_type == "percentage":

        if total <= 0:
            raise ValueError(
                "Total must be greater than zero."
            )

        percentage = (
            value / total
        ) * 100

        return {
            "calculation_type": "percentage",
            "value": value,
            "total": total,
            "percentage": round(
                percentage,
                2
            )
        }

    elif calculation_type == "percentage_difference":

        if value1 == 0 and value2 == 0:
            raise ValueError(
                "Both values cannot be zero."
            )

        average = (
            abs(value1)
            + abs(value2)
        ) / 2

        difference = abs(
            value1 - value2
        )

        percentage_difference = (
            difference / average
        ) * 100

        return {
            "calculation_type": (
                "percentage_difference"
            ),
            "value1": value1,
            "value2": value2,
            "percentage_difference": round(
                percentage_difference,
                2
            )
        }

    else:

        raise ValueError(
            "Unsupported calculation type. "
            "Use emi, simple_interest, "
            "compound_interest, percentage, "
            "or percentage_difference."
        )





# ============================================================
# BANKING ACTIONS
# ============================================================

@mcp.tool()
def freeze_account(account_number: str) -> dict:
    """
    Freeze an active bank account.

    This action changes the account status from ACTIVE to FROZEN.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/accounts/freeze",
        json={
            "account_number": account_number
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get("detail", "Account freeze failed.")
        except Exception:
            error = "Account freeze failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def unfreeze_account(account_number: str) -> dict:
    """
    Unfreeze a frozen bank account.

    This action changes the account status from FROZEN to ACTIVE.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/accounts/unfreeze",
        json={
            "account_number": account_number
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get("detail", "Account unfreeze failed.")
        except Exception:
            error = "Account unfreeze failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def update_customer_phone(
    customer_id: int,
    phone: str
) -> dict:
    """
    Update an existing customer's phone number.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/customers/phone",
        json={
            "customer_id": customer_id,
            "phone": phone
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Customer phone update failed."
            )
        except Exception:
            error = "Customer phone update failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def update_customer_email(
    customer_id: int,
    email: str
) -> dict:
    """
    Update an existing customer's email address.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/customers/email",
        json={
            "customer_id": customer_id,
            "email": email
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Customer email update failed."
            )
        except Exception:
            error = "Customer email update failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def block_card(card_id: int) -> dict:
    """
    Block an active bank card.

    This action changes the card status from ACTIVE to BLOCKED.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/cards/block",
        json={
            "card_id": card_id
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Card block failed."
            )
        except Exception:
            error = "Card block failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def unblock_card(card_id: int) -> dict:
    """
    Unblock a blocked bank card.

    This action changes the card status from BLOCKED to ACTIVE.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/cards/unblock",
        json={
            "card_id": card_id
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Card unblock failed."
            )
        except Exception:
            error = "Card unblock failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def create_support_ticket(
    customer_id: int,
    account_id: int | None,
    subject: str,
    description: str,
    category: str,
    priority: str
) -> dict:
    """
    Create a new support ticket.

    The ticket is created with OPEN status.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/tickets/create",
        json={
            "customer_id": customer_id,
            "account_id": account_id,
            "subject": subject,
            "description": description,
            "category": category,
            "priority": priority
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Support ticket creation failed."
            )
        except Exception:
            error = "Support ticket creation failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


@mcp.tool()
def update_support_ticket(
    ticket_id: int,
    status: str | None = None,
    priority: str | None = None,
    subject: str | None = None,
    description: str | None = None
) -> dict:
    """
    Update controlled fields of an existing support ticket.
    """

    response = requests.post(
        f"{FASTAPI_URL}/actions/tickets/update",
        json={
            "ticket_id": ticket_id,
            "status": status,
            "priority": priority,
            "subject": subject,
            "description": description
        },
        timeout=30
    )

    if response.status_code >= 400:
        try:
            error = response.json().get(
                "detail",
                "Support ticket update failed."
            )
        except Exception:
            error = "Support ticket update failed."

        return {
            "success": False,
            "error": error
        }

    return response.json()


    



# ============================================================
# OFFICIAL WEB SEARCH
# ============================================================

MAX_RESULTS_PER_SOURCE = 2
MAX_TOTAL_RESULTS = 5
MAX_CONTENT_LENGTH = 5000


def is_valid_url(url: str) -> bool:
    """
    Check whether the URL is a valid HTTP/HTTPS URL.
    """

    try:

        parsed = urlparse(url)

        return (
            parsed.scheme in {
                "http",
                "https"
            }
            and bool(parsed.netloc)
        )

    except Exception:

        return False


def is_official_source(url: str) -> bool:
    """
    Check whether the URL belongs to one of
    the approved official domains.
    """

    try:

        hostname = (
            urlparse(url)
            .netloc
            .lower()
            .split(":")[0]
        )

        for source in OFFICIAL_SOURCES.values():

            domain = source["domain"].lower()

            if (
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
            ):
                return True

        return False

    except Exception:

        return False


def get_source_name(url: str) -> str:
    """
    Return the official source name for a URL.
    """

    hostname = (
        urlparse(url)
        .netloc
        .lower()
        .split(":")[0]
    )

    for source in OFFICIAL_SOURCES.values():

        domain = source["domain"].lower()

        if (
            hostname == domain
            or hostname.endswith(
                "." + domain
            )
        ):
            return source["name"]

    return "Unknown"


@mcp.tool()
def search_official_web(query: str):
    if not query or not query.strip():
        return {
            "success": False,
            "error": "Search query cannot be empty."
        }

    try:
        query = query.strip()
        query_lower = query.lower()

        source_keywords = {
            "rbi": [
                "rbi",
                "reserve bank",
                "repo rate",
                "reverse repo",
                "monetary policy",
                "policy rate",
                "bank rate",
                "crr",
                "slr",
                "inflation",
                "interest rate",
                "rupee",
                "forex",
                "banking",
                "digital lending",
                "payment system"
            ],
            "npci": [
                "upi",
                "rupay",
                "fastag",
                "bharat billpay",
                "bbps",
                "imps",
                "nach",
                "aadhaar",
                "aeps",
                "upi lite",
                "upi transaction",
                "upi limit",
                "upi transaction limit",
                "transaction limit",
                "transaction limits",
                "per transaction",
                "daily limit",
                "per day",
            ],
            "sebi": [
                "sebi",
                "mutual fund",
                "stock market",
                "securities",
                "shares",
                "ipo",
                "investor",
                "broker",
                "demat",
                "insider trading",
                "capital market"
            ],
            "irdai": [
                "irdai",
                "insurance",
                "life insurance",
                "health insurance",
                "motor insurance",
                "insurer",
                "policyholder"
            ],
            "pfrda": [
                "pfrda",
                "nps",
                "national pension",
                "pension",
                "pran",
                "retirement"
            ],
            "income_tax": [
                "income tax",
                "incometax",
                "itr",
                "tax return",
                "tax slab",
                "tds",
                "tcs",
                "pan",
                "assessment",
                "taxpayer",
                "income tax department"
            ],
        }

        matched_sources = []

        for source_key, keywords in source_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                matched_sources.append(source_key)

        if not matched_sources:
            matched_sources = list(OFFICIAL_SOURCES.keys())

        targeted_queries = []

        for source_key in matched_sources:
            domain = OFFICIAL_SOURCES[source_key]["domain"]

            if source_key == "rbi":
                if any(
                    term in query_lower
                    for term in [
                        "repo rate",
                        "reverse repo",
                        "policy rate",
                        "bank rate",
                        "crr",
                        "slr",
                        "monetary policy",
                        "interest rate"
                    ]
                ):
                    targeted_queries.append(
                        (
                            source_key,
                            f"site:{domain} "
                            f"latest monetary policy policy rates {query}"
                        )
                    )
                else:
                    targeted_queries.append(
                        (source_key, f"site:{domain} {query}")
                    )

            else:
                targeted_queries.append(
                    (
                        source_key,
                        f"site:{domain} official {query}"
                    )
                )

        search_client = DDGS()

        results = []
        seen_urls = set()

        for source_key, search_query in targeted_queries:

            source = OFFICIAL_SOURCES[source_key]
            domain = source["domain"]

            try:
                search_results = search_client.text(
                    search_query,
                    max_results=MAX_RESULTS_PER_SOURCE,
                    backend="auto"
                )

                for item in search_results:
                    url = item.get("href") or item.get("url")

                    if not url:
                        continue

                    if not is_valid_url(url):
                        continue

                    if not is_official_source(url):
                        continue

                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    title = item.get("title", "").strip()
                    snippet = item.get("body", "").strip()

                    # -------------------------------------------------
                    # Fetch the actual official page content.
                    # -------------------------------------------------
                    page_content = snippet

                    try:
                        response = requests.get(
                            url,
                            timeout=10,
                            headers={
                                "User-Agent": (
                                    "Mozilla/5.0 "
                                    "(Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 "
                                    "(KHTML, like Gecko) "
                                    "Chrome/154.0 Safari/537.36"
                                )
                            }
                        )

                        if response.ok:
                            content_type = (
                                response.headers
                                .get("Content-Type", "")
                                .lower()
                            )

                            # HTML pages
                            if "text/html" in content_type:
                                from bs4 import BeautifulSoup

                                soup = BeautifulSoup(
                                    response.text,
                                    "html.parser"
                                )

                                for element in soup(
                                    [
                                        "script",
                                        "style",
                                        "noscript",
                                        "header",
                                        "footer",
                                        "nav"
                                    ]
                                ):
                                    element.decompose()

                                extracted_text = soup.get_text(
                                    separator=" ",
                                    strip=True
                                )

                                if extracted_text:
                                    page_content = extracted_text

                            # PDF pages
                            elif "application/pdf" in content_type:
                                try:
                                    reader = PdfReader(BytesIO(response.content))

                                    pdf_text = []

                                    for page in reader.pages:
                                        text = page.extract_text()

                                        if text:
                                            pdf_text.append(text)

                                    extracted_pdf_text = "\n".join(pdf_text).strip()

                                    if extracted_pdf_text:
                                        # Prioritize sections likely to contain the actual answer
                                        keywords = [
                                            "transaction limit",
                                            "per transaction",
                                            "transaction limits",
                                            "UPI limit",
                                            "₹",
                                            "lakh",
                                            "crore"
                                        ]

                                        lines = extracted_pdf_text.splitlines()

                                        relevant_lines = []

                                        for i, line in enumerate(lines):
                                            line_lower = line.lower()

                                            if any(keyword.lower() in line_lower for keyword in keywords):
                                                # Include nearby lines for context
                                                start = max(0, i - 3)
                                                end = min(len(lines), i + 4)

                                                relevant_lines.extend(lines[start:end])

                                        # Remove duplicates while preserving order
                                        relevant_lines = list(dict.fromkeys(relevant_lines))

                                        if relevant_lines:
                                            page_content = "\n".join(relevant_lines)
                                        else:
                                            page_content = extracted_pdf_text

                                    else:
                                        page_content = snippet

                                except Exception as pdf_error:
                                    print(
                                        f"Could not extract PDF {url}: "
                                        f"{type(pdf_error).__name__}: {pdf_error}",
                                        file=sys.stderr
                                    )

                                    page_content = snippet

                    except Exception as fetch_error:
                        print(
                            f"Could not fetch official page {url}: "
                            f"{type(fetch_error).__name__}: {fetch_error}",
                            file=sys.stderr
                        )

                    results.append({
                        "title": title,
                        "url": url,
                        "source": source["name"],
                        "content": page_content[:MAX_CONTENT_LENGTH]
                    })

                    if len(results) >= MAX_TOTAL_RESULTS:
                        break

            except Exception as source_error:
                print(
                    f"Official source search failed for {domain}: "
                    f"{type(source_error).__name__}: {source_error}",
                    file=sys.stderr
                )
                continue

            if len(results) >= MAX_TOTAL_RESULTS:
                break

        if not results:
            return {
                "success": False,
                "query": query,
                "error": (
                    "No relevant results were found from the "
                    "approved official sources."
                )
            }

        return {
            "success": True,
            "query": query,
            "results": results
        }

    except Exception as e:
        print(
            f"Official web search error: "
            f"{type(e).__name__}: {e}",
            file=sys.stderr
        )

        return {
            "success": False,
            "query": query,
            "error": "Official web search failed."
        }


# ============================================================
# START MCP SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run()