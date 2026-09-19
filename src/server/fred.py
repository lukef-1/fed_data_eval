from .app import db, FREDObservation
from flask import Blueprint, request, jsonify, current_app
import httpx
import json

from time import sleep
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

bp = Blueprint("fred", __name__, url_prefix="/fred")


@bp.route("/series/observations")
def get_fred_observation():

    url = "https://api.stlouisfed.org/fred/series/observations"

    args = request.args
    series_id = args.get("series_id")
    date = args.get("date")

    if series_id is None:
        return jsonify({"error": "Must provide a series_id"}), 400
    elif date is None:
        return jsonify({"error": "Must provide a date"}), 400

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Date must be in YYYY-MM-01 format"}), 400

    row = db.session.execute(
        db.select(FREDObservation).filter_by(
            series_id=series_id,
            observation_start=date_obj,
            observation_end=date_obj)
    ).scalar_one_or_none()

    if row:
        current_app.logger.info("Cache hit, returning value from DB")
        return json.loads(row.body)

    current_app.logger.info("Cache miss, calling FRED API")
    sleep(1)
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": date,
        "observation_end": date,
    }

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()

        new_observation = FREDObservation(
            series_id=series_id,
            observation_start=date_obj,
            observation_end=date_obj,
            body=response.text,
            fetched_at=datetime.now(timezone.utc),
        )
        db.session.add(new_observation)
        db.session.commit()
        return response.json()

    except httpx.HTTPError as e:
        return jsonify({"error": f"FRED returned an error: {e}"}), 502
