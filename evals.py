from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, json_dataset
from inspect_ai.scorer import includes
from inspect_ai.solver import generate, system_message

CLOSED_BOOK = """Answer in the format ANSWER: <number>
If you do not know the value, reply ANSWER: UNKNOWN"""


@task
def closed_book_test():
    return Task(
        dataset=json_dataset(
            "questions.json",
            # Using FieldSpec to get metadata fields
            FieldSpec(
                input="input",
                target="target",
                id="question_id",
                metadata=["series_id", "series_name", "period_full"],
            ),
        ),
        solver=[system_message(CLOSED_BOOK), generate()],
        scorer=includes(),  # pass if target appears in the output
    )
