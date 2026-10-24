import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY was not found in the environment."
    )


client = Groq(
    api_key=api_key
)


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    content_type: str
) -> str:
    """
    Transcribe uploaded audio using Groq Speech-to-Text.
    """

    transcription = client.audio.transcriptions.create(
        file=(
            filename,
            audio_bytes,
            content_type
        ),
        model="whisper-large-v3-turbo",
        response_format="text",
        language="en",
        temperature=0.0
    )

    return transcription.strip()