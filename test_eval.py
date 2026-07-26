from inspect_ai import Task, task
from inspect_ai.dataset import Sample, FieldSpec, hf_dataset
from inspect_ai.scorer import includes, model_graded_qa
from inspect_ai.solver import generate
from inspect_ai.dataset import json_dataset



@task
def test():
    return Task(
        dataset=json_dataset("questions.json"),
        solver=generate(),
        scorer=includes()   # pass if target appears in the output
    )