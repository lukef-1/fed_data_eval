from constants import CLOSED_BOOK_PROMPT, NoNumber, extract_number

from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, json_dataset
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    NOANSWER,
    Score,
    Target,
    accuracy,
    grouped,
    scorer,
    stderr,
    includes
)
from inspect_ai.solver import TaskState, generate, system_message


@scorer(metrics=[grouped(accuracy(), "period_full"), stderr()])
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
                explanation="No properly formatted answer was provided."
            )

        if response == NoNumber.UNKNOWN:
            return Score(
                value=NOANSWER, 
                answer=raw_response,
                explanation="Model stated that answer was unknown."
            )

        correct = abs(response - expected) <= tolerance
        print(f"Response: {response} - Expected: {expected} - Tolerance: {tolerance} - Correct: {correct}")
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=raw_response,
            explanation=state.output.completion,
        )

    return score


@task
def closed_book_test():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            # Using FieldSpec to get metadata fields
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full"],
            ),
        ),
        solver=[system_message(CLOSED_BOOK_PROMPT), generate()],
        scorer=includes()
    )

@task
def closed_book_test_custom():
    return Task(
        dataset=json_dataset(
            "../questions.json",
            # Using FieldSpec to get metadata fields
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full", "tolerance"],
            ),
        ),
        solver=[system_message(CLOSED_BOOK_PROMPT), generate()],
        scorer=within_margin()
    )
