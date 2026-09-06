"""Builds the questions.json file by making a series of FRED API calls."""

import json
import random
from dataclasses import asdict
from datetime import date, datetime
from time import sleep

import httpx
from constants import (
    API_KEY,
    FRED_START_DATE,
    FRED_URL,
    OBS_PER_PERIOD,
    RANDOM_SEED,
    SERIES,
    YEARS,
    ObservationEntry,
)

random.seed(RANDOM_SEED)


def call_fred_api(series_id: str) -> list[dict[str, str]]:
    """Return all observations from a series_id via FRED API call."""

    print(f"Calling FRED API for series: {series_id}")
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": FRED_START_DATE,
    }

    sleep(1)
    response = httpx.get(FRED_URL, params=params)
    response.raise_for_status()
    data = response.json()

    return data["observations"]


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
                    obs_date=obs["date"],
                    period_start=period_start,
                    period_end=period_end,
                    tolerance=tolerance,
                )
            )

    return final_observations


def write_to_json(all_observations: list[ObservationEntry], file_name: str) -> None:
    """Writes a list of observation entries to JSON"""
    obs_dict = [asdict(obs) for obs in all_observations]

    with open(file_name, "w") as f:
        json.dump(obs_dict, f, default=str)


def main():
    all_observations = []

    for series_id in SERIES:
        print(f"\nEvaluating new series: {series_id}")

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

    write_to_json(all_observations, "questions.json")


if __name__ == "__main__":
    main()
