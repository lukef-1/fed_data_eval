from enum import StrEnum
from typing import NamedTuple

from dataclasses import dataclass, field
from datetime import date


class NoNumber(StrEnum):
    NO_ANSWER = "no_answer"
    UNKNOWN = "unknown"
    INVALID = "invalid"


class TestType(StrEnum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"


class SeriesFields(NamedTuple):
    name: str
    tolerance: float
    units: str


@dataclass
class ObservationRaw:
    """Class for an unprocessed API response for a single series observation."""

    realtime_start: str | None
    realtime_end: str | None
    date: str
    value: float | NoNumber
    test_type: str


@dataclass
class ObservationEntry:
    """Class for a question with a golden response from an API response."""

    input: str = field(init=False)
    target: float | NoNumber
    series_id: str
    series_name: str
    units: str
    obs_date: date
    period_start: int
    period_end: int
    period_full: str = field(init=False)
    tolerance: float
    question_id: str = field(init=False)
    test_type: str

    def __post_init__(self):
        obs_date_str = self.obs_date.strftime("%B %Y")

        # Dynamically generate the prompt
        self.input = f"According to FRED data, what was the value of {self.series_name} (units: {self.units}) in the United States in {obs_date_str}?"

        # Generate a single time period field
        self.period_full = f"{self.period_start}-{self.period_end}"

        self.question_id = f"{self.series_id}_{self.obs_date}"
