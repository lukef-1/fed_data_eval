from inspect_ai import Task, task
from inspect_ai.dataset import Sample, FieldSpec, hf_dataset
from inspect_ai.scorer import includes, model_graded_qa
from inspect_ai.solver import generate


@task
def hello():
    return Task(
        dataset=[Sample(input="What currency is used in Japan? Answer in one word.",
                        target="Yen"),
                 Sample(input="What currency is used in the United States? Answer in one word.",
                        target="Dollar"),
                 Sample(input="What currency is used in Spain? Answer in one word.",
                        target="Euro")
                ],
        solver=generate(),
        scorer=includes(),   # pass if target appears in the output
    )

"""
@task
def simpleqa():
    return Task(
        dataset=hf_dataset(
            "codelion/SimpleQA-Verified",
            split="train",
            limit=5,
            sample_fields=FieldSpec(input="problem", target="answer")
        ),
        solver=generate(),
        scorer=model_graded_qa(),   # free-form answers → grade with a model
    )
"""
