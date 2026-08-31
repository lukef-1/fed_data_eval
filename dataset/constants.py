from dataclasses import dataclass, field
from datetime import date
from typing import NamedTuple

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")


class SeriesFields(NamedTuple):
    name: str
    tolerance: float
    units: str


SERIES = {
    "UNRATE": SeriesFields("Unemployment Rate", 0.101, "Percent, Seasonally Adjusted"),
    "CIVPART": SeriesFields(
        "Labor Force Participation Rate", 0.101, "Percent, Seasonally Adjusted"
    ),
    "FEDFUNDS": SeriesFields(
        "Effective Federal Funds Rate", 0.0501, "Percent, Not Seasonally Adjusted"
    ),
    "CPIAUCSL": SeriesFields(
        "Consumer Price Index: All Urban Consumers, All Items",
        0.501,
        "Index 1982-1984=100, Seasonally Adjusted",
    ),
    "CPILFESL": SeriesFields(
        "CPI: All Items Less Food and Energy",
        0.501,
        "Index 1982-1984=100, Seasonally Adjusted",
    ),
    "PAYEMS": SeriesFields(
        "Total Nonfarm Payroll Employment",
        200,
        "Thousands of Persons, Seasonally Adjusted",
    ),
    "HOUST": SeriesFields(
        "New Privately-Owned Housing Units Started",
        30,
        "Thousands of Units, Seasonally Adjusted Annual Rate",
    ),
    "INDPRO": SeriesFields(
        "Industrial Production Index", 0.501, "Index 2017=100, Seasonally Adjusted"
    ),
}

YEARS = [(2016, 2020), (2021, 2025), (2026, 2026)]
MONTHS = [m for m in range(1, 13)]
MONTHS_2026 = [m for m in range(1, 7)]

OBS_PER_PERIOD = 3

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_START_DATE = "2016-01-01"

RANDOM_SEED = 42


@dataclass
class ObservationEntry:
    """Class for a question with a golden response from an API response."""

    input: str = field(init=False)
    target: float
    series_id: str
    series_name: str
    units: str
    obs_date: date
    period_start: int
    period_end: int
    period_full: str = field(init=False)
    tolerance: float

    def __post_init__(self):
        obs_date_str = self.obs_date.strftime("%B %Y")

        # Dynamically generate the prompt
        self.input = f"According to FRED series {self.series_id} (units: {self.units}), what was the value of {self.series_name} in the United States in {obs_date_str}?"

        # Generate a single time period field
        self.period_full = f"{self.period_start}-{self.period_end}"