from evaluator.constants import extract_number
from evaluator.constants import NoNumber


def test_regex_basic():
    assert extract_number("ANSWER:  1.1") == 1.1


def test_regex_int():
    assert extract_number("ANSWER: 5") == 5.0


def test_regex_comma():
    assert extract_number("ANSWER: $150,935") == 150935.0


def test_regex_negative():
    assert extract_number("ANSWER: -2.5%") == -2.5


def test_regex_preamble():
    assert extract_number("The rate was low.\nANSWER: 3.8") == 3.8


def test_regex_no_answer_year():
    assert extract_number("I'm not able to access 2026 data.") == NoNumber.NO_ANSWER


def test_regex_unknown_upper():
    assert extract_number("ANSWER: UNKNOWN") == NoNumber.UNKNOWN


def test_regex_unknown_lower():
    assert extract_number("ANSWER: unknown") == NoNumber.UNKNOWN


def test_regex_unknown_number():
    assert (
        extract_number("ANSWER: UNKNOWN. I do not have information on 2019.")
        == NoNumber.UNKNOWN
    )


def test_regex_answer_word_no_colon():
    assert extract_number("I don't have the answer for July 2016") == NoNumber.NO_ANSWER
