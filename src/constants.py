import os

from dotenv import load_dotenv

from schema import SeriesFields, TreatmentStatus

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_START_DATE = "2016-01-01"

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
OBS_PER_PERIOD = 5

# Defines years for PRE and POST out-of-bounds samples + the number of each to include per series.
OOB_YEARS = [(1880, 1900), (2030, 2050)]
NUM_OOB_PER_CATEGORY = 2

RANDOM_SEED = 42

FLAKY_WEIGHTS = {
    TreatmentStatus.ERROR: 0.2,
    TreatmentStatus.TREATMENT_A: 0.2,
    TreatmentStatus.TREATMENT_B: 0.2,
    TreatmentStatus.NORMAL: 0.4,
}
