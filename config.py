import os
import sys

from dotenv import load_dotenv


load_dotenv()


APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "groq"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)




print(
    f"Application environment: {APP_ENV}",
    file=sys.stderr
)

print(
    f"LLM provider: {LLM_PROVIDER}",
    file=sys.stderr
)

print(
    f"LLM model: {LLM_MODEL}",
    file=sys.stderr
)

if GROQ_API_KEY:

    print(
        "Groq API key: Loaded",
        file=sys.stderr
    )

else:

    print(
        "Groq API key: NOT FOUND",
        file=sys.stderr
    )


