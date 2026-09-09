import asyncio
import json
import random
from pathlib import Path
import re

import httpx

from constants import API_KEY, FRED_URL, RANDOM_SEED, FLAKY_WEIGHTS
from schema import TreatmentStatus

random.seed(RANDOM_SEED)

CACHE_DIR = Path(__file__).parent / "_cache" / "tools"


def _get_treatment_status() -> TreatmentStatus:
    "Finds a treatment variant for a a given sample."
    variants = list(FLAKY_WEIGHTS.keys())
    weights = list(FLAKY_WEIGHTS.values())

    return random.choices(variants, weights=weights, k=1)[0]


async def _fred_observation_api_call(series_id: str, date: str) -> str | dict:
    """
    Handles the FRED API call and error handling. Returns a stringified message
    in case of an error, and returns a dictionary with the FRED date and and value.
    """

    url = FRED_URL

    cache_path = CACHE_DIR / "observations" / f"{series_id.upper()}_{date}.json"
    if cache_path.exists():
        print("\tCache Hit - Observations")
        with open(cache_path, "r") as f:
            return json.load(f)

    params = {
        "series_id": series_id.upper(),
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": date,
        "observation_end": date,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        await asyncio.sleep(1)
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as e:
            return f"Network error contacting FRED for {series_id} on {date}: {e!r}"

    if response.is_error:
        return f"Error returned for {series_id} on {date}. Error code: {response.status_code}. Error message: {response.text}"

    data = json.loads(response.text)
    observations = data["observations"]

    if not observations:
        return f"No observation found for {series_id} on {date}."

    returned_date = observations[-1]["date"]
    try:
        value = float(observations[-1]["value"])
    except ValueError as e:
        return f"ValueError - returned value was not a float - error: {e}"

    result = {"returned_date": returned_date, "returned_value": value}

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(result, f)

    return result


async def get_single_fred_value(series_id: str, date: str) -> str:
    """
    Returns the value for a specific FRED series in a specific month. Results may
    not be accurate in 100% of cases.

    Args:
        series_id: The FRED series ID to look up. Must be in abbreviated, all-caps format,
            e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
            directly by user prompts.
        date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
            For example, "August 2026" is converted to "2026-08-01".

    Returns:
        A string listing the value for the series at the requested date.
    """

    response = await _fred_observation_api_call(series_id=series_id, date=date)

    # Return stringified error messages directly
    if isinstance(response, str):
        return response

    returned_date = response["returned_date"]
    returned_value = response["returned_value"]

    return f"The value for {series_id} on {returned_date} was {returned_value}"


async def get_single_fred_value_flaky(series_id: str, date: str) -> str:
    """
    Returns the value for a specific FRED series in a specific month. Results may
    not be accurate in 100% of cases.

    Args:
        series_id: The FRED series ID to look up. Must be in abbreviated, all-caps format,
            e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
            directly by user prompts.
        date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
            For example, "August 2026" is converted to "2026-08-01".

    Returns:
        A string listing the value for the series at the requested date.
    """

    treatment_status = _get_treatment_status()
    # 20% chance of getting an outright error
    if treatment_status == TreatmentStatus.ERROR:
        return "Server error, please re-try shortly."

    response = await _fred_observation_api_call(series_id=series_id, date=date)

    # Return stringified error messages directly
    if isinstance(response, str):
        return response

    returned_date = response["returned_date"]
    returned_value = response["returned_value"]

    # Flaky conditions - 20% chance of cut-off response, 20% of multiplied value
    if treatment_status == TreatmentStatus.TREATMENT_A:
        return f"The value for {series_id} on {returned_date} is ..."
    if treatment_status == TreatmentStatus.TREATMENT_B:
        return f"The value for {series_id} on {returned_date} was {returned_value * 3}"

    return f"The value for {series_id} on {returned_date} was {returned_value}"


async def _get_series_list(search_text: str) -> str | list[str]:
    """
    Helper that fetches FRED series list results. Returns the full set, which is
    always returned by the non-flaky tool and sometimes returned in full by the
    flaky tool variant.
    """

    url = "https://api.stlouisfed.org/fred/series/search"

    cache_key = search_text.lower()
    clean_path = re.sub(r"[^a-z0-9]+", "_", cache_key)[:80]

    cache_path = CACHE_DIR / "search" / f"{clean_path}.json"
    if cache_path.exists():
        print("\tCache Hit - Series List")
        with open(cache_path, "r") as f:
            return json.load(f)

    params = {
        "api_key": API_KEY,
        "file_type": "json",
        "search_text": search_text,
        "limit": 10,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        await asyncio.sleep(1)
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as e:
            return f"Network error contacting FRED for {search_text}: {e!r}"

    if response.is_error:
        return f"Error returned when searching for {search_text}. Error code: {response.status_code}. Error message: {response.text}"

    data = json.loads(response.text)

    total_matches = data["count"]
    num_shown = data["limit"]

    if not total_matches:
        return f"No matches found for search term {search_text}."

    order_by = data["order_by"]
    sort_order = data["sort_order"]
    series = data["seriess"]

    result = []
    result.append(
        f"Showing top {num_shown} out of {total_matches} matches, ordered by {order_by} and sorted in {sort_order} order."
    )

    for row in series:
        id = row["id"]
        title = row["title"]
        obs_start = row["observation_start"]
        obs_end = row["observation_end"]
        freq = row["frequency"]
        units = row["units"]
        adjust = row["seasonal_adjustment"]
        popularity = row["popularity"]

        result.append(
            f"Series ID: {id} - Title: {title} - Observations from {obs_start} to {obs_end} - Frequency {freq} - Units {units} {adjust} - Popularity {popularity}"
        )

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(result, f)

    return result


async def get_fred_series_list(search_text: str) -> str:
    """
    Returns an ordered list of FRED series for a given search term, with
    flexibility to determine ordering. Results may not be accurate in 100% of cases.

    Args:
        search_text: The words to match against economic data series. Required.

    Returns:
        A string listing the top 10 results (if 10+ matches exist).
    """

    response = await _get_series_list(search_text=search_text)

    # Return stringified error messages directly
    if isinstance(response, str):
        return response

    return "\n".join(response)


async def get_fred_series_list_flaky(search_text: str) -> str:
    """
    Returns an ordered list of FRED series for a given search term, with
    flexibility to determine ordering. Results may not be accurate in 100% of cases.

    Args:
        search_text: The words to match against economic data series. Required.

    Returns:
        A string listing the top 10 results (if 10+ matches exist).
    """

    treatment_status = _get_treatment_status()
    # 20% chance of getting an outright error
    if treatment_status == TreatmentStatus.ERROR:
        return "Server error, please re-try shortly."

    response = await _get_series_list(search_text=search_text)

    # Return stringified error messages directly
    if isinstance(response, str):
        return response

    full_str = "\n".join(response)

    # Flaky conditions: 20% chance of cut-off response, 20% of reversed list
    if treatment_status == TreatmentStatus.TREATMENT_A:
        shortened_length = int(len(full_str) * 0.1)
        return full_str[:shortened_length] + "..."
    if treatment_status == TreatmentStatus.TREATMENT_B:
        response_reversed = response[::-1]
        return "\n".join(response_reversed)

    return full_str
