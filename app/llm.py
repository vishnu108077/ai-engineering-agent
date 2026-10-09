
from dotenv import load_dotenv
from google import genai

# Load variables from the project's .env file.
load_dotenv()

# The Gemini SDK reads GEMINI_API_KEY from the environment.
client = genai.Client()


def ask_ai(question: str) -> str:
    """Send a question to Gemini and return its response."""
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=question,
    )

    return interaction.output_text
