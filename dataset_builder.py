from dotenv import load_dotenv 
import os

import httpx
from time import sleep
import json
from datetime import date, datetime

from dataclasses import asdict
import random

from dataset_constants import (
    ObservationEntry,
    SERIES,
    TOLERANCES,
    YEARS,
    MONTHS,
    OBS_PER_PERIOD,
    FRED_URL,
    FRED_START_DATE
)

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")


def call_fred_api(series_id: str) -> list[dict[str, str]]:
    """Return all observations from a series_id via FRED API call."""

    print(f"Calling FRED API for series: {series_id}")
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": FRED_START_DATE
    }

    url = FRED_URL
    sleep(1)

    response = httpx.get(url, params=params)
    data = json.loads(response.text)
    return data.get("observations")


def get_random_period_dates(period_start: int, period_end: int) -> list[date]:
    """
    Pick random Month-Year combinations within a given range of a start year to 
    an end year. Skips any duplicates.
    """

    period_dates = []

    while len(period_dates) < OBS_PER_PERIOD:
        year = random.randint(period_start, period_end)
        month = random.choice(MONTHS)
        selected = date(year, month, 1)

        # Add selected dates to list if not already present
        if selected not in period_dates:
            period_dates.append(selected)
        else:
            print("\t\tDuplicate - skipping", selected)

    return period_dates


def get_random_observations(
        all_observations: list[dict[str, str]],
        series_id: str
        ) -> list[ObservationEntry]:
    """Select a random subset of observations from specified time periods."""

    series_name = SERIES[series_id]
    tolerance = TOLERANCES[series_id]
    random.seed(42)

    obs_list = []

    # Loop through each year range
    for period_start, period_end in YEARS:
        print(f"Evaluating series: {series_id} for {period_start} - {period_end}")

        period_dates = get_random_period_dates(period_start, period_end)

        for obs in all_observations:
            # Convert observation date to a datetime date
            obs_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
            if obs_date in period_dates:
                print(f"Date match: {obs_date}")
                target = float(obs["value"])

                obs_list.append(ObservationEntry(
                    target = target,
                    series_id = series_id,
                    series_name = series_name,
                    obs_date = obs_date,
                    period_start = period_start,
                    period_end = period_end,
                    tolerance = tolerance
                    )
                )

    return obs_list


def write_to_json(
        all_observations: list[ObservationEntry],
        file_name: str) -> None:
    """Writes a list of observation entries to JSON"""
    obs_dict = [asdict(obs) for obs in all_observations]

    with open(file_name, "a") as f:
        json.dump(obs_dict, f)


def main():
    all_observations = []
    for series_id in SERIES:
        print("-------------------------")
        print(f"Evaluating new series: {series_id}")
        # Make API call
        series_observations = call_fred_api(series_id)

        # Randomly select observations from each period
        all_observations.extend(get_random_observations(
            series_observations,
            series_id)
        )
        #print("All observations:", all_observations)
        
    # Write results to JSON
    write_to_json(all_observations, "questions.json")

if __name__ == "__main__":
    main()