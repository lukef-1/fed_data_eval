"""Builds the questions.json file by making a series of FRED API calls."""

import json
import random
import re
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from time import sleep

import httpx

from constants import (
    API_KEY,
    FRED_START_DATE,
    FRED_URL,
    NUM_OOB_PER_CATEGORY,
    OBS_PER_PERIOD,
    OOB_YEARS,
    RANDOM_SEED,
    SERIES,
    YEARS,
)
from schema import NoNumber, ObservationEntry, ObservationRaw, TestType

random.seed(RANDOM_SEED)

CACHE_DIR = Path(__file__).parent / "_cache"


def get_cache_path(fred_url: str, params: dict[str, str]) -> Path:
    "Turns a URL and parameters into a path for caching API call results."

    Path.mkdir(CACHE_DIR, exist_ok=True)

    params_cache = {k: v for k, v in params.items() if k != "api_key"}
    url = httpx.URL(fred_url)

    merged_url = str(url.copy_with(params=params_cache)).lower()
    merged_url_short = merged_url.replace(FRED_URL, "")
    merged_url_clean = re.sub(r'[<>:"/\\|?*&=]', "_", merged_url_short)

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


class SeriesDatasetLoader:
    def __init__(
        self,
        series_observations: list[dict[str, str]],
        series_id: str,
        series_name: str,
        tolerance: float,
        units: str,
        obs_per_period: int,
    ):

        self.series_observations = series_observations
        self.series_id = series_id
        self.series_name = series_name
        self.tolerance = tolerance
        self.units = units
        self.obs_per_period = obs_per_period

        # Temporarily holds all observations from each period
        self.year_buckets: dict[tuple, list[ObservationRaw]] = {
            period: [] for period in YEARS + OOB_YEARS
        }
        self.sampled_observations: dict[tuple, list[ObservationRaw]] = {
            period: [] for period in YEARS + OOB_YEARS
        }
        self.final_observations: list[ObservationEntry] = []

    def sort_observations(self) -> None:
        """
        Sort all observations for a series into lists according to each time period.
        """

        for observation in self.series_observations:
            if observation["value"] == ".":
                continue

            obs_raw = ObservationRaw(
                realtime_start=observation.get("realtime_start"),
                realtime_end=observation.get("realtime_end"),
                date=datetime.strptime(observation["date"], "%Y-%m-%d").date(),
                value=float(observation["value"]),
                test_type=TestType.IN_SCOPE.value,
            )

            obs_date = datetime.strptime(observation["date"], "%Y-%m-%d")

            for period_start, period_end in YEARS:
                if period_start <= obs_date.year <= period_end:
                    self.year_buckets[(period_start, period_end)].append(obs_raw)

    def get_sampled_observations(self) -> None:
        """
        Select a random subset of observations for each time period.
        """

        for (period_start, period_end), bucket in self.year_buckets.items():
            # Skip empty lists for out-of-bounds observations
            if not bucket:
                continue
            print(f"Sampling for period: {period_start} - {period_end}")

            random_observations = random.sample(bucket, self.obs_per_period)
            self.sampled_observations[(period_start, period_end)].extend(
                random_observations
            )

    def add_out_of_bounds_entries(self) -> None:
        """
        Add entries with invalid dates and invalid expected answers to the list
        of sampled observations.
        """

        for period_start, period_end in OOB_YEARS:
            observations: list[ObservationRaw] = []
            possible_dates = [
                (m, y)
                for m in range(1, 13)
                for y in range(period_start, period_end + 1)
            ]

            random_dates = random.sample(possible_dates, k=NUM_OOB_PER_CATEGORY)
            for month, year in random_dates:
                d = datetime(year, month, 1).date()

                observations.append(
                    ObservationRaw(
                        realtime_start=None,
                        realtime_end=None,
                        date=d,
                        value=NoNumber.INVALID,
                        test_type=TestType.OUT_OF_SCOPE.value,
                    )
                )

            self.sampled_observations[(period_start, period_end)] = observations

    def build_observation_entries(self) -> None:
        """
        Turns a list of sampled observations into a list of final SeriesObservations.
        """

        for (
            period_start,
            period_end,
        ), observations in self.sampled_observations.items():
            for observation in observations:
                self.final_observations.append(
                    ObservationEntry(
                        input=self._get_prompt(observation.date),
                        target=observation.value,
                        series_id=self.series_id,
                        series_name=self.series_name,
                        units=self.units,
                        obs_date=observation.date,
                        period_start=period_start,
                        period_end=period_end,
                        tolerance=self.tolerance,
                        test_type=observation.test_type,
                    )
                )

    def _get_prompt(self, obs_date: date) -> str:
        "Randomly assigns one of three prompt variants to a question."

        path = random.randint(1, 3)
        date_clean = obs_date.strftime("%B %Y")
        if path == 1:
            return f"According to FRED data, what was the value of {self.series_name} (units: {self.units}) in the United States in {date_clean}?"
        if path == 2:
            return f"In the US, what was the value of {self.series_name} (units: {self.units}) in {date_clean}?"
        if path == 3:
            return (
                f"US value of {self.series_name} units: {self.units}) in {date_clean}?"
            )

        return "Randomization error"


def write_to_json(all_observations: list[ObservationEntry], file_name: str) -> None:
    "Writes all select observations across series to a JSON file."

    obs_dict = [asdict(obs) for obs in all_observations]

    with open(file_name, "w") as f:
        json.dump(obs_dict, f, default=str)


def main():
    all_observations = []

    for series_id in SERIES:
        print(f"\n--- Evaluating new series: {series_id} ---")

        series_observations = call_fred_api(series_id)

        series_loader = SeriesDatasetLoader(
            series_observations=series_observations,
            series_id=series_id,
            series_name=SERIES[series_id].name,
            tolerance=SERIES[series_id].tolerance,
            units=SERIES[series_id].units,
            obs_per_period=OBS_PER_PERIOD,
        )

        series_loader.sort_observations()
        series_loader.get_sampled_observations()
        series_loader.add_out_of_bounds_entries()
        series_loader.build_observation_entries()

        all_observations.extend(series_loader.final_observations)

    write_to_json(all_observations, "questions.json")


if __name__ == "__main__":
    main()
