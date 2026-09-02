from constants import (
    CLOSED_BOOK_PROMPT,
    TOOL_PROMPT,
    WEB_SEARCH_PROMPT,
    NoNumber,
    extract_number,
    FRED_URL,
    API_KEY,
)

import asyncio
import httpx
import json

from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, json_dataset
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    NOANSWER,
    Score,
    Target,
    accuracy,
    frequency,
    grouped,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState, generate, system_message, use_tools
from inspect_ai.tool import tool, web_search


@scorer(metrics=[grouped(accuracy(), "period_full"), frequency(), stderr()])
def within_margin():
    """Custom scorer documentation: https://inspect.aisi.org.uk/custom-scorers.html"""

    async def score(state: TaskState, target: Target) -> Score:
        raw_response = state.output.completion
        # Load tolerance value for specific series
        tolerance = state.metadata["tolerance"]

        response = extract_number(raw_response)
        expected = float(target.text)

        if response == NoNumber.NO_ANSWER:
            return Score(
                value=INCORRECT,
                answer=raw_response,
                explanation="No properly formatted answer was provided.",
            )

        if response == NoNumber.UNKNOWN:
            return Score(
                value=NOANSWER,
                answer=raw_response,
                explanation="Model stated that answer was unknown.",
            )

        correct = abs(response - expected) <= tolerance
        explanation = f"Response: {response} - Expected: {expected} - Tolerance: {tolerance} - Correct: {correct}"
        print(explanation)
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=raw_response,
            explanation=explanation,
        )

    return score


@tool
def call_fred_api():
    async def get_single_fred_value(series_id: str, date: str) -> str:
        """
        Returns the value for a specific FRED series in a specific month.

        Args:
            series_id: The FRED series ID to look up. Must be in abbrevatied, all-caps format,
                e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
                directly by user prompts.
            date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
                For example, "August 2026" is coverted to "2026-08-01".

        Returns:
            A string listing the value for the series at the requested date.
        """

        params = {
            "series_id": series_id.upper(),
            "api_key": API_KEY,
            "file_type": "json",
            "observation_start": date,
            "observation_end": date,
        }

        async with httpx.AsyncClient() as client:
            await asyncio.sleep(0.5)
            response = await client.get(FRED_URL, params=params)

        if response.is_error:
            return f"Error returned for {series_id} on {date}. Error code: {response.status_code}. Error message: {response.text}"

        data = json.loads(response.text)
        observations = data["observations"]

        if not observations:
            return f"No observation found for {series_id} on {date}."

        date = observations[-1]["date"]
        value = observations[-1]["value"]

        return f"The value for {series_id} on {date} was {value}"

    return get_single_fred_value


@task
def closed_book_test_custom():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full", "tolerance"],
            ),
        ),
        solver=[system_message(CLOSED_BOOK_PROMPT), generate()],
        scorer=within_margin(),
    )


@task
def fred_api_test_custom():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full", "tolerance"],
            ),
        ),
        solver=[system_message(TOOL_PROMPT), use_tools(call_fred_api()), generate()],
        scorer=within_margin(),
    )


@task
def web_search_test_custom():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full", "tolerance"],
            ),
        ),
        solver=[system_message(WEB_SEARCH_PROMPT), use_tools(web_search()), generate()],
        scorer=within_margin(),
    )
