import uuid
import time

import requests
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

FASTAPI_URL = "http://127.0.0.1:8000"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Banking Assistant",
    page_icon="🏦",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Move the Send button slightly upward */
    div[data-testid="column"]:has(button[kind="primary"]) {
        transform: translateY(-6px);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_input" not in st.session_state:
    st.session_state.message_input = ""

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None


# ============================================================
# FUNCTIONS
# ============================================================

def create_new_chat():
    """
    Reset the session state to start a new chat.
    """
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.message_input = ""
    st.session_state.pending_message = None
    st.session_state.last_audio_id = None
    st.session_state.pending_action = None
    

def stream_message(message: str, thread_id: str):
    response = requests.post(
        f"{FASTAPI_URL}/chat/stream",
        json={
            "message": message,
            "thread_id": thread_id
        },
        stream=True,
        timeout=120
    )

    response.raise_for_status()

    for chunk in response.iter_content(
        chunk_size=None,
        decode_unicode=True
    ):
        if chunk:
            yield chunk


def stream_message_for_display(message: str, thread_id: str):
    for chunk in stream_message(message, thread_id):
        if chunk:
            yield chunk
            time.sleep(0.04)


def render_message(content: str):
    """
    Render a message while making source URLs clickable.
    """
    if not content:
        return

    lines = content.splitlines()
    source_lines = []
    normal_lines = []

    in_sources = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower() in {"sources", "**sources**"}:
            in_sources = True
            normal_lines.append(line)
            continue

        if in_sources and stripped.startswith("http"):
            source_lines.append(stripped)
        else:
            normal_lines.append(line)

    st.markdown("\n".join(normal_lines), unsafe_allow_html=False)

    if source_lines:
        st.markdown("### Sources")

        for url in source_lines:
            st.markdown(f"[Open official source ↗]({url})")

def transcribe_audio(audio_bytes: bytes):
    """
    Send recorded audio to FastAPI for transcription.
    """

    response = requests.post(
        f"{FASTAPI_URL}/transcribe",
        files={
            "file": (
                "recording.wav",
                audio_bytes,
                "audio/wav"
            )
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()["transcript"]


def fetch_pending_action(thread_id: str):
    """
    Fetch a pending state-changing action for the current conversation.
    """
    response = requests.get(
        f"{FASTAPI_URL}/actions/pending/{thread_id}",
        timeout=30
    )

    response.raise_for_status()

    return response.json().get("pending_action")


def get_action_confirmation_text(pending_action: dict):
    """
    Convert a pending action into a user-friendly confirmation message.
    """

    tool_name = pending_action.get("tool_name")
    arguments = pending_action.get("arguments", {})

    if tool_name == "freeze_account":
        return (
            "Are you sure you want to **freeze this account?**\n\n"
            f"**Account Number:** `{arguments.get('account_number', '')}`"
        )

    if tool_name == "unfreeze_account":
        return (
            "Are you sure you want to **unfreeze this account?**\n\n"
            f"**Account Number:** `{arguments.get('account_number', '')}`"
        )

    if tool_name == "update_customer_phone":
        return (
            "Are you sure you want to **update the customer's phone number?**\n\n"
            f"**Customer ID:** `{arguments.get('customer_id', '')}`\n\n"
            f"**New Phone:** `{arguments.get('phone', '')}`"
        )

    if tool_name == "update_customer_email":
        return (
            "Are you sure you want to **update the customer's email address?**\n\n"
            f"**Customer ID:** `{arguments.get('customer_id', '')}`\n\n"
            f"**New Email:** `{arguments.get('email', '')}`"
        )

    if tool_name == "block_card":
        return (
            "Are you sure you want to **block this card?**\n\n"
            f"**Card ID:** `{arguments.get('card_id', '')}`"
        )

    if tool_name == "unblock_card":
        return (
            "Are you sure you want to **unblock this card?**\n\n"
            f"**Card ID:** `{arguments.get('card_id', '')}`"
        )

    if tool_name == "create_support_ticket":
        return (
            "Are you sure you want to **create this support ticket?**\n\n"
            f"**Customer ID:** `{arguments.get('customer_id', '')}`\n\n"
            f"**Category:** `{arguments.get('category', '')}`\n\n"
            f"**Priority:** `{arguments.get('priority', '')}`\n\n"
            f"**Subject:** {arguments.get('subject', '')}"
        )

    if tool_name == "update_support_ticket":
        return (
            "Are you sure you want to **update this support ticket?**\n\n"
            f"**Ticket ID:** `{arguments.get('ticket_id', '')}`\n\n"
            f"**Status:** `{arguments.get('status', '')}`\n\n"
            f"**Priority:** `{arguments.get('priority', '')}`"
        )

    return "Are you sure you want to perform this action?"



@st.dialog("Confirm Action")
def show_action_confirmation():
    pending_action = st.session_state.pending_action

    if not pending_action:
        return

    st.markdown(
        get_action_confirmation_text(pending_action)
    )

    st.warning(
        "This action will make a change to your banking data."
    )

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:

        if st.button(
            "Confirm",
            use_container_width=True,
            type="primary"
        ):

            try:

                response = requests.post(
                    f"{FASTAPI_URL}/actions/confirm",
                    json={
                        "thread_id": st.session_state.thread_id
                    },
                    timeout=120
                )

                response.raise_for_status()

                data = response.json()

                if not data.get("success"):
                    st.error(
                        data.get(
                            "error",
                            "The action could not be completed."
                        )
                    )
                    return

                result = data.get("result", {})

                assistant_response = ""

                for message in reversed(
                    result.get("messages", [])
                ):

                    if message.get("type") == "ai":

                        content = message.get(
                            "content",
                            ""
                        )

                        if content:
                            assistant_response = content
                            break

                if assistant_response:

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_response
                        }
                    )

                st.session_state.pending_action = None

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Could not confirm the action: {exc}"
                )

    with cancel_col:

        if st.button(
            "Cancel",
            use_container_width=True
        ):

            try:

                response = requests.post(
                    f"{FASTAPI_URL}/actions/cancel",
                    json={
                        "thread_id": st.session_state.thread_id
                    },
                    timeout=30
                )

                response.raise_for_status()

                data = response.json()

                if not data.get("success"):
                    st.error(
                        data.get(
                            "error",
                            "The action could not be cancelled."
                        )
                    )
                    return

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Action cancelled. No changes were made."
                    }
                )

                st.session_state.pending_action = None

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Could not cancel the action: {exc}"
                )




def fetch_conversations():
    response = requests.get(
        f"{FASTAPI_URL}/conversations",
        timeout=30
    )
    response.raise_for_status()
    return response.json()["conversations"]


def get_conversation_group(updated_at: str):
    updated = datetime.fromisoformat(
        updated_at.replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    if updated.date() == now.date():
        return "Today"

    if (now.date() - updated.date()).days == 1:
        return "Yesterday"

    return "Older"


def fetch_conversation(thread_id: str):
    response = requests.get(
        f"{FASTAPI_URL}/conversations/{thread_id}",
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def load_conversation(thread_id: str):
    """
    Load a conversation from the backend and update the session state.
    """
    data = fetch_conversation(thread_id)

    st.session_state.thread_id = thread_id
    st.session_state.messages = data["messages"]
    st.session_state.pending_message = None
    st.session_state.pending_action = None
    st.session_state.message_input = ""
    st.session_state.last_audio_id = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🏦 Banking Assistant")

    st.button(
        "＋ New Chat",
        use_container_width=True,
        on_click=create_new_chat
    )

    st.divider()

    try:
        conversations = fetch_conversations()

        if conversations:
            grouped_conversations = {
                "Today": [],
                "Yesterday": [],
                "Older": []
            }

            for conversation in conversations:
                group = get_conversation_group(
                    conversation["updated_at"]
                )
                grouped_conversations[group].append(conversation)

            for group_name in ["Today", "Yesterday", "Older"]:
                group_conversations = grouped_conversations[group_name]

                if not group_conversations:
                    continue

                st.subheader(group_name)

                for conversation in group_conversations:
                    thread_id = conversation["thread_id"]
                    title = conversation["title"]

                    is_active = (
                        thread_id == st.session_state.thread_id
                    )

                    button_label = (
                        f"▶ {title}"
                        if is_active
                        else title
                    )

                    if st.button(
                        button_label,
                        key=f"conversation_{thread_id}",
                        use_container_width=True
                    ):
                        try:
                            load_conversation(thread_id)
                            st.rerun()
                        except Exception as exc:
                            st.error(
                                f"Could not load conversation: {exc}"
                            )

        else:
            st.caption("No previous conversations yet.")

    except Exception as exc:
        st.error(
            f"Could not load conversations: {exc}"
        )


# ============================================================
# HEADER
# ============================================================

st.title("🏦 Banking Assistant")

st.caption(
    "Ask questions about your accounts, transactions, "
    "customers, support tickets, or general banking topics."
)


# ============================================================
# PROCESS PENDING MESSAGE
#
# IMPORTANT:
# This happens BEFORE rendering the conversation.
#
# Therefore, when the user presses Send:
#
# Send → rerun → process message → render updated chat
#
# The new user message will NEVER appear underneath
# the composer while waiting for the response.
# ============================================================


# ============================================================
# CONVERSATION HISTORY
#
# THIS IS INTENTIONALLY BEFORE THE COMPOSER.
# ============================================================

if st.session_state.messages:

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                render_message(message["content"])
            else:
                st.markdown(message["content"])

else:

    st.info(
        "👋 Start a conversation by typing a message "
        "or using the microphone."
    )


# NEW streaming response
if st.session_state.pending_message:
    pending_message = st.session_state.pending_message
    st.session_state.pending_message = None

    # Add the user message to the stored history.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": pending_message
        }
    )

    # Display the new user message immediately.
    with st.chat_message("user"):
        st.markdown(pending_message)

    try:
        # Stream the assistant response.
        with st.chat_message("assistant"):
            assistant_response = st.write_stream(
                stream_message_for_display(
                    pending_message,
                    st.session_state.thread_id
                )
            )

        # Store the completed response for future reruns.
        # Action requests stop at the confirmation node, so
        # they may not have an assistant response yet.
        if assistant_response:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_response
                }
            )

        # Check whether the backend created a pending action.
        pending_action = fetch_pending_action(
            st.session_state.thread_id
        )

        if pending_action:
            st.session_state.pending_action = pending_action

    except Exception as exc:
        error_message = (
            "Sorry, I couldn't process your request.\n\n"
            f"Error: {str(exc)}"
        )

        with st.chat_message("assistant"):
            st.markdown(error_message)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": error_message
            }
        )

    st.session_state.message_input = ""


# ============================================================
# ACTION CONFIRMATION
# ============================================================

if st.session_state.pending_action:
    show_action_confirmation()


# ============================================================
# COMPOSER
# ============================================================

st.divider()

text_col, mic_col, send_col = st.columns(
    [10, 0.55, 0.55],
    gap="small",
    vertical_alignment="bottom"
)


# ------------------------------------------------------------
# MICROPHONE
#
# We process the microphone BEFORE creating the text area.
# This allows the transcript to be placed directly into the
# editable text box.
# ------------------------------------------------------------

with mic_col:

    audio = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        use_container_width=False,
        key="voice_recorder"
    )


# ------------------------------------------------------------
# HANDLE NEW AUDIO
# ------------------------------------------------------------

if audio:

    audio_id = audio.get("id")

    if audio_id != st.session_state.last_audio_id:

        st.session_state.last_audio_id = audio_id

        try:

            with st.spinner("Transcribing..."):

                transcript = transcribe_audio(
                    audio["bytes"]
                )

            if transcript:

                # Put transcript directly into editable input.
                st.session_state.message_input = transcript

            else:

                st.warning(
                    "I couldn't detect any speech in the recording."
                )

        except Exception as exc:

            st.error(
                f"Transcription failed: {str(exc)}"
            )


# ------------------------------------------------------------
# TEXT INPUT
# ------------------------------------------------------------

with text_col:

    message_value = st.text_area(
        "Message",
        key="message_input",
        placeholder="Type your message or use the 🎙️ microphone...",
        height=70,
        label_visibility="collapsed"
    )


# ------------------------------------------------------------
# SEND BUTTON
# ------------------------------------------------------------

with send_col:

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] {
            transform: translateY(-8px);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    send_clicked = st.button(
        "↑",
        use_container_width=True,
        type="primary"
    )


# ============================================================
# SEND
# ============================================================

if send_clicked:

    message = message_value.strip()

    if not message:

        st.warning("Please enter a message.")

    else:

        # Don't process the request in this same rendering pass.
        #
        # Instead:
        # 1. Store it as pending
        # 2. Rerun
        # 3. Process it BEFORE rendering the conversation
        #
        # This keeps the UI clean.

        st.session_state.pending_message = message

        st.rerun()