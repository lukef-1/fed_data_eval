from dataclasses import dataclass, field
from datetime import date

SERIES = {
    "UNRATE": "Unemployment Rate",
    "CIVPART": "Labor Force Participation Rate",
    "FEDFUNDS": "Effective Federal Funds Rate",
    "CPIAUCSL": "Consumer Price Index: All Urban Consumers, All Items",
    "CPILFESL": "CPI: All Items Less Food and Energy",
    "PAYEMS":   "Total Nonfarm Payroll Employment",
    "HOUST":    "New Privately-Owned Housing Units Started",
    "INDPRO":   "Industrial Production Index"
}

TOLERANCES = {
    "UNRATE": 0.1,
    "CIVPART": 0.1,
    "FEDFUNDS": 0.05,
    "CPIAUCSL": 0.5,
    "CPILFESL": 0.5,
    "PAYEMS": 200,
    "HOUST": 30,
    "INDPRO": 0.5
}

YEARS = [(2015, 2019), (2020, 2024), (2025, 2025)]
MONTHS = [m for m in range(1, 13)]
OBS_PER_PERIOD = 3

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_START_DATE = "2015-01-01"


@dataclass
class ObservationEntry:
    """Class for a question with a golden response from an API response."""
    input: str = field(init=False)
    target: float
    series_id: str
    series_name: str
    obs_date: date | str
    period_start: int
    period_end: int
    tolerance: float

    def __post_init__(self):
        # Define the input field value based on results
        obs_date_str = self.obs_date.strftime("%B %Y")
        self.input = f"What was the {self.series_name} in the United States in {obs_date_str}? Answer with only the number."

        # Update obs_date to string for JSON parsing - TODO: Clean up because this is janky
        self.obs_date = str(self.obs_date)