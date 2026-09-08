from constants import FRED_URL, API_KEY, RANDOM_SEED

import json
import httpx
import asyncio

import random

random.seed(RANDOM_SEED)

async def get_single_fred_value(series_id: str, date: str) -> str:
    """
    Returns the value for a specific FRED series in a specific month.

    Args:
        series_id: The FRED series ID to look up. Must be in abbreviated, all-caps format,
            e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
            directly by user prompts.
        date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
            For example, "August 2026" is converted to "2026-08-01".

    Returns:
        A string listing the value for the series at the requested date.
    """

    params = {
        "series_id": series_id.upper(),
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": date,
        "observation_end": date,
    }

    async with httpx.AsyncClient() as client:
        await asyncio.sleep(0.5)
        response = await client.get(FRED_URL, params=params)

    if response.is_error:
        return f"Error returned for {series_id} on {date}. Error code: {response.status_code}. Error message: {response.text}"

    data = json.loads(response.text)
    observations = data["observations"]

    if not observations:
        return f"No observation found for {series_id} on {date}."

    date = observations[-1]["date"]
    value = observations[-1]["value"]

    return f"The value for {series_id} on {date} was {value}"


async def get_single_fred_value_flaky(series_id: str, date: str) -> str:
    """
    Returns the value for a specific FRED series in a specific month.

    Args:
        series_id: The FRED series ID to look up. Must be in abbreviated, all-caps format,
            e.g. GDPC1 to represent Real Gross Domestic Product. These IDs are provided
            directly by user prompts.
        date: The month to find data for in YYYY-MM-DD format. Days will always be "01".
            For example, "August 2026" is converted to "2026-08-01".

    Returns:
        A string listing the value for the series at the requested date.
    """

    if random.random() >= 0.75:
        return "API call error, please retry."

    params = {
        "series_id": series_id.upper(),
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": date,
        "observation_end": date,
    }

    async with httpx.AsyncClient() as client:
        await asyncio.sleep(0.5)
        response = await client.get(FRED_URL, params=params)

    if response.is_error:
        return f"Error returned for {series_id} on {date}. Error code: {response.status_code}. Error message: {response.text}"

    data = json.loads(response.text)
    observations = data["observations"]

    if not observations:
        return f"No observation found for {series_id} on {date}."

    date = observations[-1]["date"]
    value = observations[-1]["value"]

    return f"The value for {series_id} on {date} was {value}"


async def get_fred_series_list(search_text: str, order_by: str = "search_rank", sort_order: str = "desc") -> str:
    """
    Returns an ordered list of FRED series for a given search term, with 
    flexibility to determine ordering.

    Args:
        search_text: The words to match against economic data series. Required.
        order_by: Order results by values of the specified attribute. One 
            of the following strings: 'search_rank', 'series_id', 'title', 
            'units', 'frequency', 'seasonal_adjustment', 'realtime_start', 
            'realtime_end', 'last_updated', 'observation_start', 'observation_end', 
            'popularity', 'group_popularity'. Optional, defaults to 'search_rank'.
        sort_order: Sets whether results are in ascending ("asc") or descending 
            ("desc) order for attribute values specified by order_by. Optional, default = "desc" 
            if order_by is "search_rank" or "popularity" and Default = "asc" otherwise.    

    Returns:
        A string listing the top 10 results (if 10+ matches exist).
    """

    url = "https://api.stlouisfed.org/fred/series/search"

    params = {
        "api_key": API_KEY,
        "file_type": "json",
        "search_text": search_text,
        "limit": 10,
        "order_by": order_by,
        "sort_order": sort_order
        }

    async with httpx.AsyncClient() as client:
        await asyncio.sleep(0.5)
        response = await client.get(url, params=params)

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

    return_text = []
    return_text.append(f"Showing top {num_shown} out of {total_matches} matches, ordered by {order_by} and sorted in {sort_order} order.")

    for row in series:
        id = row["id"]
        title = row["title"]
        obs_start = row["observation_start"]
        obs_end = row["observation_end"]
        freq = row["frequency"]
        units = row["units"]
        adjust = row["seasonal_adjustment"]
        popularity = row["popularity"]

        return_text.append(f"Series ID: {id} - Title: {title} - Observations from {obs_start} to {obs_end} - Frequency {freq} - Units {units} {adjust} - Popularity {popularity}")

    return "\n".join(return_text)
