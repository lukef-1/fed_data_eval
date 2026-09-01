import re
from enum import Enum

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


CLOSED_BOOK_PROMPT = """Answer in the format ANSWER: <number>
If you do not know the value, reply ANSWER: UNKNOWN"""

TOOL_PROMPT = """Use the get_data() tool with the provided parameters to find the value.
Answer in the format ANSWER: <number>."""

WEB_SEARCH_PROMPT = """Use the web_search() tool to find the value.
Answer in the format ANSWER: <number>."""


class NoNumber(Enum):
    NO_ANSWER = "no answer"
    UNKNOWN = "unknown"


def extract_number(text: str) -> float | NoNumber:
    """Extracts a number or non-answer string from an LLM response."""

    text = text.lower()

    if "answer" not in text:
        return NoNumber.NO_ANSWER

    # Remove commas up front to make regex easier
    answer = text.split("answer:")[-1].replace(",", "")
    if "unknown" in answer:
        return NoNumber.UNKNOWN

    match = re.search(r"-?\d+\.?\d*", answer)
    if match:
        match_str = match.group()
        return float(match_str)

    return NoNumber.NO_ANSWER
