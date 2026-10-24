from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.requests import Request
from pydantic import BaseModel
from api.database_service import (
    get_account_by_number,
    get_database_connection,
    get_transactions_by_account,
    get_customer_by_id,
    get_tickets_by_customer,
    get_loans_by_customer,
    get_cards_by_customer,
    get_beneficiaries_by_customer,
    get_all_branches,
    create_support_ticket,
    freeze_account,
    unfreeze_account,
    update_customer_phone,
    update_customer_email,
    block_card,
    unblock_card,
    update_support_ticket
)
import uuid
from services.speech_service import transcribe_audio
from graph.agent_graph import (
    invoke_agent_graph,
    stream_final_agent_response,
    get_agent_conversation_history,
    get_pending_action,
    confirm_pending_action,
    cancel_pending_action
)

from services.conversation_service import (
    create_conversation_if_not_exists,
    get_all_conversations,
    get_conversation,
    update_conversation
)

app = FastAPI(
    title="VG Bank API",
    description="Banking API for the GenAI Banking Assistant V2",
    version="1.0.0"
)

# This defines the expected JSON structure when someone creates a support ticket.
class SupportTicketRequest(BaseModel):
    customer_id: int
    account_id: int | None = None
    subject: str
    description: str
    category: str
    priority: str


class FreezeAccountRequest(BaseModel):
    account_number: str


class UnfreezeAccountRequest(BaseModel):
    account_number: str


class UpdateCustomerPhoneRequest(BaseModel):
    customer_id: int
    phone: str


class UpdateCustomerEmailRequest(BaseModel):
    customer_id: int
    email: str


class BlockCardRequest(BaseModel):
    card_id: int


class UnblockCardRequest(BaseModel):
    card_id: int


class UpdateSupportTicketRequest(BaseModel):
    ticket_id: int
    status: str | None = None
    priority: str | None = None
    subject: str | None = None
    description: str | None = None

# It defines what /chat expects
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

class ActionConfirmationRequest(BaseModel):
    thread_id: str

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    """
    Handle unexpected API errors in one place.
    """

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred."
        }
    )


@app.get("/")
def root():
    return {
        "message": "VG Bank API is running",
        "version": "1.0.0"
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio using Groq Speech-to-Text.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No audio file provided."
        )

    try:

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty."
            )

        transcript = transcribe_audio(
            audio_bytes,
            file.filename,
            file.content_type or "audio/wav"
        )

        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="No speech could be detected."
            )

        return {
            "success": True,
            "transcript": transcript
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(exc)}"
        )



@app.post("/conversations")
def create_new_conversation():
    thread_id = str(uuid.uuid4())

    return {
        "success": True,
        "thread_id": thread_id
    }


@app.get("/conversations")
def list_conversations():
    conversations = get_all_conversations()

    return {
        "success": True,
        "conversations": conversations
    }


@app.get("/conversations/{thread_id}")
def get_conversation_details(thread_id: str):
    conversation = get_conversation(thread_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    history = get_agent_conversation_history(thread_id)

    return {
        "success": True,
        "conversation": conversation,
        "messages": history["messages"]
    }



@app.post("/chat")
def chat(request: ChatRequest):
    """
    Send a user message to the V2 multi-agent LangGraph
    and return the final assistant response.
    """

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    thread_id = request.thread_id

    if not thread_id:
        thread_id = str(uuid.uuid4())

    result = invoke_agent_graph(
        request.message,
        thread_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )

    messages = result["result"]["messages"]

    if not messages:
        raise HTTPException(
            status_code=500,
            detail="Agent returned no messages."
        )

    final_message = messages[-1]

    return {
        "success": True,
        "thread_id": thread_id,
        "response": final_message.content,
        "route": result["result"].get("route")
    }



@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    thread_id = request.thread_id

    if not thread_id:
        thread_id = str(uuid.uuid4())

    title = request.message.strip()

    if len(title) > 50:
        title = title[:50].rstrip() + "..."

    create_conversation_if_not_exists(
        thread_id=thread_id,
        title=title
    )

    update_conversation(
        thread_id=thread_id
    )

    def generate():
        try:
            for chunk in stream_final_agent_response(
                request.message,
                thread_id
            ):
                if chunk:
                    yield chunk

        except Exception as exc:
            print(
                f"Streaming Chat error: "
                f"{type(exc).__name__}: {exc}"
            )
            yield "\n\nSorry, I couldn't process your request."

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "X-Thread-ID": thread_id
        }
    )



@app.get("/accounts/{account_number}")
def get_account(account_number: str):
    """
    Return account information for the given account number.
    """

    account = get_account_by_number(account_number)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    return dict(account)

@app.get("/accounts/{account_number}/transactions")
def get_account_transactions(
    account_number: str,
    start_date: str | None = None,
    end_date: str | None = None
):
    """
    Return transactions for an account.
    """

    account = get_account_by_number(account_number)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    transactions = get_transactions_by_account(
        account_number,
        start_date,
        end_date
    )

    return {
        "account_number": account_number,
        "transaction_count": len(transactions),
        "transactions": [
            dict(transaction)
            for transaction in transactions
        ]
    }

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    """
    Return customer information for the given customer ID.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return dict(customer)


@app.get("/customers/{customer_id}/tickets")
def get_customer_tickets(customer_id: int):
    """
    Return support tickets for the given customer.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    tickets = get_tickets_by_customer(customer_id)

    return {
        "customer_id": customer_id,
        "ticket_count": len(tickets),
        "tickets": [
            dict(ticket)
            for ticket in tickets
        ]
    }

@app.get("/customers/{customer_id}/loans")
def get_customer_loans(customer_id: int):
    """
    Return loans for the given customer.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    loans = get_loans_by_customer(customer_id)

    return {
        "customer_id": customer_id,
        "loan_count": len(loans),
        "loans": [
            dict(loan)
            for loan in loans
        ]
    }


@app.get("/customers/{customer_id}/cards")
def get_customer_cards(customer_id: int):
    """
    Return cards for the given customer.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    cards = get_cards_by_customer(customer_id)

    return {
        "customer_id": customer_id,
        "card_count": len(cards),
        "cards": [
            dict(card)
            for card in cards
        ]
    }


@app.get("/customers/{customer_id}/beneficiaries")
def get_customer_beneficiaries(customer_id: int):
    """
    Return beneficiaries for the given customer.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    beneficiaries = get_beneficiaries_by_customer(customer_id)

    return {
        "customer_id": customer_id,
        "beneficiary_count": len(beneficiaries),
        "beneficiaries": [
            dict(beneficiary)
            for beneficiary in beneficiaries
        ]
    }

@app.get("/branches")
def get_branches():
    """
    Return all active banking branches.
    """

    branches = get_all_branches()

    return {
        "branch_count": len(branches),
        "branches": [
            dict(branch)
            for branch in branches
        ]
    }

@app.post("/customers/{customer_id}/tickets")
def create_customer_ticket(
    customer_id: int,
    ticket: SupportTicketRequest
):
    """
    Create a new support ticket for a customer.
    """

    customer = get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    if ticket.customer_id != customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID in request body does not match URL"
        )

    ticket_id = create_support_ticket(
        customer_id=customer_id,
        account_id=ticket.account_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority
    )

    return {
        "message": "Support ticket created successfully",
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "status": "OPEN"
    }



# ============================================================
# Action Confirmation Endpoints
# ============================================================


@app.get("/actions/pending/{thread_id}")
def get_pending_action_for_thread(thread_id: str):
    """
    Return the pending state-changing action for a conversation.
    """

    pending_action = get_pending_action(
        thread_id
    )

    return {
        "success": True,
        "pending_action": pending_action
    }


@app.post("/actions/confirm")
def confirm_action(
    request: ActionConfirmationRequest
):
    """
    Confirm and execute the pending state-changing action.
    """

    result = confirm_pending_action(
        request.thread_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


@app.post("/actions/cancel")
def cancel_action(
    request: ActionConfirmationRequest
):
    """
    Cancel the pending state-changing action.
    """

    result = cancel_pending_action(
        request.thread_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result



# ============================================================
# Banking Action Endpoints
# ============================================================

@app.post("/actions/accounts/freeze")
def action_freeze_account(request: FreezeAccountRequest):
    """
    Freeze an active bank account.
    """

    try:
        account = freeze_account(request.account_number)

        return {
            "success": True,
            "message": "Account frozen successfully.",
            "account": dict(account)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/accounts/unfreeze")
def action_unfreeze_account(request: UnfreezeAccountRequest):
    """
    Unfreeze a frozen bank account.
    """

    try:
        account = unfreeze_account(request.account_number)

        return {
            "success": True,
            "message": "Account unfrozen successfully.",
            "account": dict(account)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/customers/phone")
def action_update_customer_phone(
    request: UpdateCustomerPhoneRequest
):
    """
    Update a customer's phone number.
    """

    try:
        customer = update_customer_phone(
            request.customer_id,
            request.phone
        )

        return {
            "success": True,
            "message": "Customer phone number updated successfully.",
            "customer": dict(customer)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/customers/email")
def action_update_customer_email(
    request: UpdateCustomerEmailRequest
):
    """
    Update a customer's email address.
    """

    try:
        customer = update_customer_email(
            request.customer_id,
            request.email
        )

        return {
            "success": True,
            "message": "Customer email address updated successfully.",
            "customer": dict(customer)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/cards/block")
def action_block_card(request: BlockCardRequest):
    """
    Block an active card.
    """

    try:
        card = block_card(request.card_id)

        return {
            "success": True,
            "message": "Card blocked successfully.",
            "card": dict(card)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/cards/unblock")
def action_unblock_card(request: UnblockCardRequest):
    """
    Unblock a blocked card.
    """

    try:
        card = unblock_card(request.card_id)

        return {
            "success": True,
            "message": "Card unblocked successfully.",
            "card": dict(card)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/tickets/create")
def action_create_ticket(
    ticket: SupportTicketRequest
):
    """
    Create a support ticket.
    """

    try:
        customer = get_customer_by_id(ticket.customer_id)

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found."
            )

        

        ticket_id = create_support_ticket(
            customer_id=ticket.customer_id,
            account_id=ticket.account_id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority
        )

        return {
            "success": True,
            "message": "Support ticket created successfully.",
            "ticket_id": ticket_id,
            "customer_id": ticket.customer_id,
            "status": "OPEN"
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


@app.post("/actions/tickets/update")
def action_update_ticket(
    request: UpdateSupportTicketRequest
):
    """
    Update controlled fields of a support ticket.
    """

    try:
        ticket = update_support_ticket(
            ticket_id=request.ticket_id,
            status=request.status,
            priority=request.priority,
            subject=request.subject,
            description=request.description
        )

        return {
            "success": True,
            "message": "Support ticket updated successfully.",
            "ticket": dict(ticket)
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )