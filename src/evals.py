from constants import FRED_URL, API_KEY

from scoring import (
    CLOSED_BOOK_PROMPT,
    TOOL_PROMPT,
    TOOL_NO_ID_PROMPT,
    WEB_SEARCH_PROMPT,
    NoNumber,
    extract_number,
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
        expected = target.text

        if (expected == NoNumber.INVALID.value) and (response == NoNumber.INVALID):
            return Score(
                value=CORRECT,
                answer=raw_response,
                explanation="Model correctly identified an invalid request.",
            )

        if (expected == NoNumber.INVALID.value) or (response == NoNumber.INVALID):
            return Score(
                value=INCORRECT,
                answer=raw_response,
                explanation="Invalid incorrectly expected / returned",
            )

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

        correct = abs(response - float(expected)) <= tolerance
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
            series_id: The FRED series ID to look up. Must be in abbreviated, all-caps format,
                e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
                directly by user prompts.
            date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
                For example, "August 2026" is converted to "2026-08-01".

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


@tool
def search_fred_series():
    async def get_fred_series_list(search_text: str, order_by: str = "search_rank", sort_order: str = "desc") -> str:
        """
        Returns the value for a specific FRED series in a specific month.

        Args:
            search_text: The words to match against economic data series
            order_by: Order results by values of the specified attribute. One 
                of the following strings: 'search_rank', 'series_id', 'title', 
                'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 
                'realtime_end', 'last_updated', 'observation_start', 'observation_end', 
                'popularity', 'group_popularity'. Defaults to 'search_rank'.
            sort_order: Sets whether results are in ascending ("asc") or descending 
                ("desc) order for attribute values specified by order_by. Default = "desc" 
                if order_by is "search_rank" or "popularity" and Default = "asc" otherwise.    

        Returns:
            A string listing the top 10 results (if 10+ matches exist).
        """

        url = "https://api.stlouisfed.org/fred/series/search"

        params = {
            "api_key": API_KEY,
            "file_type": "json",
            "search_text": search_text,
            "limit": 10,
            "order_by": order_by,
            "sort_order": sort_order
            }

        async with httpx.AsyncClient() as client:
            await asyncio.sleep(0.5)
            response = await client.get(url, params=params)

        if response.is_error:
            return f"Error returned when searching for {search_text}. Error code: {response.status_code}. Error message: {response.text}"

        data = json.loads(response.text)

        total_matches = data["count"]
        num_shown = data["limit"]

        if not total_matches:
            return f"No matches found for search term {search_text}."

        order_by = data["order_by"]
        sort_order = data["sort_order"]

        series = data["seriess"]

        return_text = []
        return_text.append(f"Showing top {num_shown} out of {total_matches} matches, ordered by {order_by} and sorted in {sort_order} order.")

        for row in series:
            id = row["id"]
            title = row["title"]
            obs_start = row["observation_start"]
            obs_end = row["observation_end"]
            freq = row["frequency"]
            units = row["units"]
            adjust = row["seasonal_adjustment"]
            popularity = row["popularity"]

            return_text.append(f"Series ID: {id} - Title: {title} - Observations from {obs_start} to {obs_end} - Frequency {freq} - Units {units} {adjust} - Popularity {popularity}")

        return "\n".join(return_text)
    return get_fred_series_list


@task
def closed_book_test_custom():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=[
                    "series_id",
                    "series_name",
                    "period_full",
                    "tolerance",
                    "test_type",
                ],
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
                metadata=[
                    "series_id",
                    "series_name",
                    "period_full",
                    "tolerance",
                    "test_type",
                ],
            ),
        ),
        solver=[system_message(TOOL_PROMPT), use_tools(call_fred_api()), generate()],
        scorer=within_margin(),
    )

@task
def fred_api_test_custom_no_series():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=[
                    "series_id",
                    "series_name",
                    "period_full",
                    "tolerance",
                    "test_type",
                ],
            ),
        ),
        solver=[system_message(TOOL_NO_ID_PROMPT), use_tools(search_fred_series(), call_fred_api()), generate()],
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
                metadata=[
                    "series_id",
                    "series_name",
                    "period_full",
                    "tolerance",
                    "test_type",
                ],
            ),
        ),
        solver=[system_message(WEB_SEARCH_PROMPT), use_tools(web_search()), generate()],
        scorer=within_margin(),
    )
