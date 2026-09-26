from enum import StrEnum
from datetime import date

import json
import random

class TreatmentStatus(StrEnum):
    ERROR = "error"
    TRUNCATED = "truncated"
    INCORRECT = "incorrect"
    NORMAL = "normal"


FLAKY_WEIGHTS = {
    TreatmentStatus.ERROR: 0.2,
    TreatmentStatus.TRUNCATED: 0.2,
    TreatmentStatus.INCORRECT: 0.2,
    TreatmentStatus.NORMAL: 0.4,
}


def _assign_treatment(series_id: str, date: date) -> TreatmentStatus:
    """
    Assigns a test case to a treatment group, using seeding to consistently 
    put the same observation in the same group.
    """
    # Ensure upper case for all series_ids
    series_id_upper = series_id.upper()

    seed_str = f"{series_id_upper}-{date}"
    random.seed(seed_str)

    variants = list(FLAKY_WEIGHTS.keys())
    weights = list(FLAKY_WEIGHTS.values())

    return random.choices(variants, weights=weights, k=1)[0]


def _normal_treatment(observation_text: str) -> str:
    "Passthrough case - return the same API response."
    return observation_text


def _error_treatment(observation_text: str) -> str:
    return json.dumps({"error": "The server returned an error."})


def _truncated_treatment(observation_text: str) -> str:
    "Truncated case - replace the observation number with '...'"
    observation_dict = json.loads(observation_text)
    observation_dict["observations"][0]["value"] = '...'

    return json.dumps(observation_dict)


def _incorrect_treatment(observation_text:str) -> str:
    "Incorrect case - triple the observation number (x3)"
    observation_dict = json.loads(observation_text)
    try:
        value = float(observation_dict["observations"][0]["value"])
    except ValueError:
        raise ValueError("Observation value must be a number.")
    
    observation_dict["observations"][0]["value"] = round(value*3, 2)

    return json.dumps(observation_dict)

