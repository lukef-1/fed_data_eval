import os

from flask import Flask, request, jsonify

from time import sleep
import httpx

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route("/fred/series/observations")
    def get_fred_observation():

        url = "https://api.stlouisfed.org/fred/series/observations"

        args = request.args
        series_id = args.get("series_id")
        date = args.get("date")
        error = None

        if series_id is None:
            error = "Must provide a series_id"
        elif date is None:
            error = "Not yet built - Must provide date in YYYY-MM-01 format"

        if error:
            return jsonify({"error": error}), 400

        app.logger.info("Calling the FRED API...")
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
            return response.json()
        except httpx.HTTPError as e:
            return jsonify({"error": f"FRED returned an error: {e}"}), 502

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
