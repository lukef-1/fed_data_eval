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
from inspect_ai.tool import tool

from scoring import (
    CLOSED_BOOK_PROMPT,
    TOOL_NO_ID_PROMPT,
    TOOL_PROMPT,
    NoNumber,
    extract_number,
)
from tools import (
    get_fred_series_list,
    get_fred_series_list_flaky,
    get_single_fred_value,
    get_single_fred_value_flaky,
)


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
    return get_single_fred_value


@tool(name="call_fred_api")
def call_fred_api_flaky():
    return get_single_fred_value_flaky


@tool
def search_fred_series():
    return get_fred_series_list


@tool(name="search_fred_series")
def search_fred_series_flaky():
    return get_fred_series_list_flaky


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
            shuffle=True,
            seed=42,
        ),
        solver=[
            system_message(TOOL_NO_ID_PROMPT),
            use_tools(search_fred_series(), call_fred_api()),
            generate(),
        ],
        scorer=within_margin(),
    )


@task
def fred_api_test_custom_no_series_flaky():
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
            shuffle=True,
            seed=42,
        ),
        solver=[
            system_message(TOOL_NO_ID_PROMPT),
            use_tools(search_fred_series_flaky(), call_fred_api_flaky()),
            generate(),
        ],
        scorer=within_margin(),
    )
