from .app import db, FREDObservation
from flask import Blueprint, request, jsonify, current_app, Response
from sqlalchemy.exc import IntegrityError
import httpx
import json

from time import sleep
from datetime import datetime, date, timezone

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

bp = Blueprint("fred", __name__, url_prefix="/fred")


def _validate_observation_args(series_id: str | None, date: str | None) -> tuple:
    """
    Validates that a series_id exists as a parsable string and that a date
    exists as a parsable date.
    """
    current_app.logger.info("Passing API call args through validator")

    if not series_id:
        current_app.logger.info("Validator error: blank series_id")
        return ((jsonify({"error": "Must provide a series_id"}), 400), "error")
    elif not date:
        current_app.logger.info("Validator error: blank date")
        return ((jsonify({"error": "Must provide a date"}), 400), "error")

    series_id_upper = series_id.upper()

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        current_app.logger.info("Validator error: date can't be parsed as a date")
        return ((jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400), "error")

    return (series_id_upper, date_obj), None


def _get_clean_observation(series_id: str, date: date) -> str:
    """
    For a series_id and date, returns the results as text. Raises errors directly
    if encountered on the API calls.
    """

    # Check for value in DB cache
    row = db.session.execute(
        db.select(FREDObservation).filter_by(
            series_id=series_id,
            observation_start=date,
            observation_end=date,
        )
    ).scalar_one_or_none()

    if row:
        current_app.logger.info("Cache hit, returning value from DB")
        return row.body

    # Call FRED API if no cached value is found
    current_app.logger.info("Cache miss, calling FRED API")
    url = "https://api.stlouisfed.org/fred/series/observations"

    sleep(0.5)
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": date,
        "observation_end": date,
    }

    response = httpx.get(url, params=params, timeout=30.0)
    current_app.logger.info(f"FRED response received, {response.text[:50]}...")
    response.raise_for_status()

    observation = FREDObservation(
        series_id=series_id,
        observation_start=date,
        observation_end=date,
        body=response.text,
        fetched_at=datetime.now(timezone.utc),
    )
    _write_to_observations_table(observation)
    return response.text


def _write_to_observations_table(observation: FREDObservation):
    "Attempts to write a new FRED Observation record to the database."
    try:
        db.session.add(observation)
        db.session.commit()
        current_app.logger.info("Wrote new observation record to DB")
    except IntegrityError as e:
        current_app.logger.warning(f"Database write returned an error: {e}")
        db.session.rollback()
        current_app.logger.info("Integrity exception caught, rolling back.")


@bp.route("/series/observations")
def get_fred_observation():
    """
    E2E coordinator for the view. Coordinates input validation, calls a helper
    to get a clean observation (or a raised error), then responds with the result.
    """

    args = request.args
    series_id = args.get("series_id")
    date = args.get("date")
    current_app.logger.info(f"New API call: series: {series_id}, date: {date}")

    validation_resp, error = _validate_observation_args(series_id, date)
    if error:
        current_app.logger.info("Validation error, returning that directly")
        return validation_resp

    series_id_upper, date_obj = validation_resp
    try:
        observation = _get_clean_observation(series_id=series_id_upper, date=date_obj)
        return Response(
            response=observation, 
            headers={"Content-Type": "application/json"}, 
            status=200)

    except httpx.HTTPStatusError as e:
        return jsonify(
            {
                "error": "FRED returned an error.",
                "upstream_status": e.response.status_code,
                "upstream_error_message": e.response.text,
            }
        ), 502

    except httpx.HTTPError:
        return jsonify({"error": "Could not reach FRED server"}), 502
