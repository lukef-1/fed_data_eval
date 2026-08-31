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
    MONTHS,
    MONTHS_2026,
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

    # `observations` key contains a list of all periods and data
    return data.get("observations")


def get_random_period_dates(period_start: int, period_end: int) -> list[date]:
    """
    Pick random Month-Year combinations within a given range of a start year to
    an end year. Skips any duplicates.
    """

    period_dates = []

    while len(period_dates) < OBS_PER_PERIOD:
        year = random.randint(period_start, period_end)
        if year == 2026:
            month = random.choice(MONTHS_2026)
        else:
            month = random.choice(MONTHS)
        selected = date(year, month, 1)

        # Add selected dates to list if not already present
        if selected not in period_dates:
            period_dates.append(selected)
        else:
            print("\t\tDuplicate - skipping", selected)

    return period_dates


def get_random_observations(
    series_observations: list[dict[str, str]],
    series_id: str,
    series_name: str,
    tolerance: float,
    units: str,
) -> list[ObservationEntry]:
    """Select a random subset of observations from specified time periods."""

    obs_list = []

    # Loop through each year range
    for period_start, period_end in YEARS:
        print(f"Evaluating series: {series_id} for {period_start} - {period_end}")

        period_dates = get_random_period_dates(period_start, period_end)

        for obs in series_observations:
            # Convert observation date to a datetime date
            obs_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
            if obs_date in period_dates:
                print(f"Date match: {obs_date}")

                # FRED uses "." for unknown values - skip those cases
                if obs["value"] == ".":
                    continue
                else:
                    target = float(obs["value"])

                obs_list.append(
                    ObservationEntry(
                        target=target,
                        series_id=series_id,
                        series_name=series_name,
                        units=units,
                        obs_date=obs_date,
                        period_start=period_start,
                        period_end=period_end,
                        tolerance=tolerance,
                    )
                )

    return obs_list


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

        series_observations = call_fred_api(series_id)

        all_observations.extend(
            get_random_observations(
                series_observations, series_id, series_name, tolerance, units
            )
        )

    write_to_json(all_observations, "questions.json")


if __name__ == "__main__":
    main()