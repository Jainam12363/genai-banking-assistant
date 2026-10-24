from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


BASE_DIR = Path(__file__).resolve().parents[1]

CHECKPOINT_DATABASE_PATH = (
    BASE_DIR / "conversation_checkpoints.db"
)


def create_checkpointer():
    """
    Create the SQLite checkpointer used to persist
    LangGraph conversation state.
    """

    return SqliteSaver.from_conn_string(
        str(CHECKPOINT_DATABASE_PATH)
    )