from server.faults import (
    _assign_treatment,
    _normal_treatment,
    _error_treatment,
    _incorrect_treatment, 
    _truncated_treatment)

from datetime import datetime
import json

DATE_1 = datetime.strptime("2019-02-01", "%Y-%m-%d").date()
DATE_2 = datetime.strptime("2021-12-01", "%Y-%m-%d").date()
DATE_3 = datetime.strptime("2024-08-01", "%Y-%m-%d").date()

SERIES_1 = "UNRATE"
SERIES_2 = "CIVPART"
SERIES_3 = "FEDFUNDS"

OBSERVATION_1 = '{"realtime_start":"2026-09-20","realtime_end":"2026-09-20","observation_start":"2019-03-01","observation_end":"2019-03-01","units":"lin","output_type":1,"file_type":"json","order_by":"observation_date","sort_order":"asc","count":1,"offset":0,"limit":100000,"observations":[{"realtime_start":"2026-09-20","realtime_end":"2026-09-20","date":"2019-03-01","value":"3.8"}]}'

OBSERVATION_2 = '{"realtime_start":"2026-09-20","realtime_end":"2026-09-20","observation_start":"2023-02-02","observation_end":"2023-02-02","units":"lin","output_type":1,"file_type":"json","order_by":"observation_date","sort_order":"asc","count":1,"offset":0,"limit":100000,"observations":[{"realtime_start":"2026-09-20","realtime_end":"2026-09-20","date":"2023-02-01","value":"3.6"}]}'

def _get_value(response: str) -> float | str:
    response_dict = json.loads(response)
    return response_dict["observations"][0]["value"]

def test_randomization_basic():
    assert _assign_treatment(SERIES_1, DATE_1) == _assign_treatment(SERIES_1, DATE_1)
    assert _assign_treatment(SERIES_2, DATE_2) == _assign_treatment(SERIES_2, DATE_2)
    assert _assign_treatment(SERIES_3, DATE_3) == _assign_treatment(SERIES_3, DATE_3)


def test_randomization_casing():
    assert _assign_treatment(SERIES_1.lower(), DATE_1) == _assign_treatment(SERIES_1, DATE_1)
    assert _assign_treatment(SERIES_2.lower(), DATE_2) == _assign_treatment(SERIES_2, DATE_2)
    assert _assign_treatment(SERIES_3.lower(), DATE_3) == _assign_treatment(SERIES_3, DATE_3)


def test_normal_treatment():
    assert _normal_treatment(OBSERVATION_1) == OBSERVATION_1
    assert _normal_treatment(OBSERVATION_2) == OBSERVATION_2


def test_error_treatment():
    assert _error_treatment(OBSERVATION_1) == '{"error": "The server returned an error."}'

def test_truncated_treatment():
    resp_1 = _truncated_treatment(OBSERVATION_1)
    assert _get_value(resp_1) == '...'

    resp_2 = _truncated_treatment(OBSERVATION_2)
    assert _get_value(resp_2) == '...'


def test_incorrect_treatment():
    threshold = 0.005

    original_tripled_1 = float(_get_value(OBSERVATION_1)) * 3
    resp_1 = _get_value(_incorrect_treatment(OBSERVATION_1))
    assert abs(original_tripled_1 - float(resp_1)) <= threshold

    original_tripled_2 = float(_get_value(OBSERVATION_2)) * 3
    resp_2 = _get_value(_incorrect_treatment(OBSERVATION_2))
    assert abs(original_tripled_2 - float(resp_2)) <= threshold
