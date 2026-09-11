import re

from schema import NoNumber

CLOSED_BOOK_PROMPT = """Answer in the format ANSWER: <number>
If you do not know the value, reply ANSWER: UNKNOWN. If the question asks about a
date that is not available in St. Louis Fed (FRED) data, reply ANSWER: INVALID"""

TOOL_PROMPT = """Use the call_fred_api() tool with the provided parameters to find the value. Answer in the format ANSWER: <number>.  If you do not know the value, reply "ANSWER: UNKNOWN". If the question asks about a date that is not available in St. Louis Fed (FRED) data, reply ANSWER: INVALID"""

TOOL_NO_ID_PROMPT = """Use the search_fred_series() to find the most relevant St. Louis Fed series for a user's question, then use call_fred_api() tool with the provided parameters to find the value. Answer in the format ANSWER: <number>. If you do not know the value, reply "ANSWER: UNKNOWN". If the question asks about a date that is not available in St. Louis Fed (FRED) data, reply ANSWER: INVALID"""

TOOL_NO_ID_LOOSE_PROMPT = """Answer in the format ANSWER: <number>. If you do not know the value, reply "ANSWER: UNKNOWN". If the question asks about a date that is not available, reply ANSWER: INVALID"""


def extract_number(text: str) -> float | NoNumber:
    """Extracts a number or non-answer string from an LLM response."""

    text = text.lower()

    if "answer:" not in text:
        return NoNumber.NO_ANSWER

    # Remove commas up front to make regex easier
    answer = text.split("answer:")[-1].replace(",", "")
    if "unknown" in answer:
        return NoNumber.UNKNOWN

    if "invalid" in answer:
        return NoNumber.INVALID

    match = re.search(r"-?\d+\.?\d*", answer)
    if match:
        match_str = match.group()
        return float(match_str)

    return NoNumber.NO_ANSWER
