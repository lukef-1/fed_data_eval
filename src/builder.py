"""Builds the questions.json file by making a series of FRED API calls."""

import json
import random
from dataclasses import asdict
from datetime import datetime
from time import sleep

from pathlib import Path

import httpx
from .constants import (
    API_KEY,
    FRED_START_DATE,
    FRED_URL,
    OBS_PER_PERIOD,
    RANDOM_SEED,
    SERIES,
    YEARS,
    OOB_RANGES,
    NUM_OOB_PER_CATEGORY
)

from .schema import ObservationRaw, ObservationEntry, NoNumber, TestType

random.seed(RANDOM_SEED)

CACHE_DIR = Path(__file__).parent / "_cache"

def get_cache_path(fred_url: str, params: dict[str, str]) -> Path:
    "Turns a URL and parameters into a path for caching API call results."

    Path.mkdir(CACHE_DIR, exist_ok=True)

    params_cache = {k: v for k, v in params.items() if k != "api_key"}
    url = httpx.URL(fred_url)

    merged_url = str(url.copy_with(params=params_cache)).lower()
    merged_url_clean = merged_url.replace(FRED_URL, "")

    return Path(CACHE_DIR / merged_url_clean)


def call_fred_api(series_id: str) -> list[dict[str, str]]:
    """Return all observations from a series_id via FRED API call."""

    print(f"Calling FRED API for series: {series_id}")
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": FRED_START_DATE,
    }

    cache_path = get_cache_path(FRED_URL, params)

    if cache_path.exists():
        print("Cache hit!")
        with open(cache_path, "r") as f:
            data = f.read()

    else:
        print("No cache hit, calling API")
        sleep(1)
        response = httpx.get(FRED_URL, params=params)
        response.raise_for_status()

        with open(cache_path, "w") as f:
            f.write(response.text)
            data = response.text

    data_dict = json.loads(data)
    return data_dict["observations"]


# LOTS OF PASSING VARIABLES AROUND, MAKE A CLASS?

class SeriesDatasetLoader:
    def __init__(
            self,
            series_observations: list[dict[str, str]],
            series_id: str, 
            series_name: str,
            tolerance: float,
            units: str
            ):
        
        self.series_observations = series_observations
        self.series_id = series_id
        self.series_name = series_name
        self.tolerance = tolerance
        self.units = units

        # Temporarily holds all observations from each period
        self.year_buckets: dict[tuple, list[ObservationRaw]] = {period: [] for period in YEARS}
        self.sampled_observations: dict[tuple, list[ObservationRaw]] = {period: [] for period in YEARS}
        self.final_observations: list[ObservationEntry] = []

    def sort_observations(self) -> None:
        """
        Select a random subset of observations from a single series using specified
        time periods.
        """

        # Build list of all observations per period
        for observation in self.series_observations:
            if observation["value"] == ".":
                continue

            obs_date = datetime.strptime(observation["date"], "%Y-%m-%d")

            obs_raw = ObservationRaw(
                realtime_start = observation.get("realtime_start"),
                realtime_end = observation.get("realtime_end"),
                date = observation["date"],
                value = float(observation["value"]),
                test_type = TestType.IN_SCOPE.value
            )

            for period_start, period_end in YEARS:
                if period_start <= obs_date.year <= period_end:
                    self.year_buckets[(period_start, period_end)].append(obs_raw)

        return None

    def get_random_observations(self) -> None:
        for (period_start, period_end), bucket in self.year_buckets.items():
            print(f"Sampling for period: {period_start} - {period_end}")

            random_observations = random.sample(bucket, OBS_PER_PERIOD)
            self.sampled_observations[(period_start, period_end)].extend(random_observations)

    def add_out_of_bounds_entries(self) -> None:

        for period_start, period_end in OOB_RANGES:
            observations: list[ObservationRaw] = []

            for _ in range(NUM_OOB_PER_CATEGORY):
                year = random.randint(period_start, period_end)
                month = random.randint(1, 12)
                d = datetime(year, month, 1).date()

                observations.append(
                    ObservationRaw(
                        realtime_start=None,
                        realtime_end=None,
                        date=d.strftime("%Y-%m-%d"),
                        value=NoNumber.INVALID,
                        test_type=TestType.OUT_OF_SCOPE.value
                    )
                )

            self.sampled_observations[(period_start, period_end)] = observations


    def build_observation_entries(self) -> None:
        for (period_start, period_end), observations in self.sampled_observations.items():

            for observation in observations:
                self.final_observations.append(
                    ObservationEntry(
                        target=observation.value,
                        series_id=self.series_id,
                        series_name=self.series_name,
                        units=self.units,
                        obs_date=datetime.strptime(observation.date, "%Y-%m-%d").date(),
                        period_start=period_start,
                        period_end=period_end,
                        tolerance=self.tolerance,
                        test_type=observation.test_type
                    )
                )


def get_random_observations(
    series_observations: list[dict[str, str]],
    series_id: str,
    series_name: str,
    tolerance: float,
    units: str,
) -> list[ObservationEntry]:
    """
    Select a random subset of observations from a single series using specified
    time periods.
    """

    buckets = {period: [] for period in YEARS}
    final_observations = []

    # Build list of all observations per period
    for observation in series_observations:
        if observation["value"] == ".":
            continue

        obs_date = datetime.strptime(observation["date"], "%Y-%m-%d")
        year = obs_date.year

        for period_start, period_end in YEARS:
            if period_start <= year <= period_end:
                buckets[(period_start, period_end)].append(observation)

    # Sample from each period's observations list
    for (period_start, period_end), bucket in buckets.items():
        print(f"Sampling for period: {period_start} - {period_end}")
        sampled_observations = random.sample(bucket, OBS_PER_PERIOD)

        for obs in sampled_observations:
            final_observations.append(
                ObservationEntry(
                    target=float(obs["value"]),
                    series_id=series_id,
                    series_name=series_name,
                    units=units,
                    obs_date=datetime.strptime(obs["date"], "%Y-%m-%d").date(),
                    period_start=period_start,
                    period_end=period_end,
                    tolerance=tolerance,
                    test_type=TestType.IN_SCOPE.value
                )
            )
  
    return final_observations


def add_out_of_bounds(
    series_id: str,
    series_name: str,
    tolerance: float,
    units: str,
) -> list[ObservationEntry]:
    """Adds out-of-bounds observations for PRE and POST valid date entries."""

    print("Adding out-of-bounds observations")
    oob_observations = []

    for start_year, end_year in OOB_RANGES:
        for _ in range(NUM_OOB_PER_CATEGORY):
            year = random.randint(start_year, end_year)
            month = random.randint(1, 12)

            oob_observations.append(
                ObservationEntry(
                    target=NoNumber.INVALID,
                    series_id=series_id,
                    series_name=series_name,
                    units=units,
                    obs_date = datetime(year, month, 1).date(),
                    period_start=start_year,
                    period_end=end_year,
                    tolerance=tolerance,
                    test_type=TestType.OUT_OF_SCOPE.value
                )
            )

    return oob_observations


def write_to_json(all_observations: list[ObservationEntry], file_name: str) -> None:
    """Writes a list of observation entries to JSON"""
    obs_dict = [asdict(obs) for obs in all_observations]

    with open(file_name, "w") as f:
        json.dump(obs_dict, f, default=str)


def main():
    all_observations = []

    for series_id in SERIES:
        print(f"\n--- Evaluating new series: {series_id} ---")

        series_name = SERIES[series_id].name
        tolerance = SERIES[series_id].tolerance
        units = SERIES[series_id].units

        # Get all series observations
        series_observations = call_fred_api(series_id)

        # Add random observations to final list
        all_observations.extend(
            get_random_observations(
                series_observations, series_id, series_name, tolerance, units
            )
        )

        all_observations.extend(
            add_out_of_bounds(series_id, series_name, tolerance, units)
        )

    write_to_json(all_observations, "questions.json")


if __name__ == "__main__":
    main()
