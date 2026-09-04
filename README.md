# fed_data_eval

An LLM Evaluation using [Inspect AI](https://inspect.aisi.org.uk/) to measure how accurately models report US macroeconomic data from 2016 to 2026. Questions are generated using the [FRED API](https://fred.stlouisfed.org/docs/api/fred/).

## Repo structure

```
dataset/
  builder.py          Pulls FRED observations and writes questions.json
  constants.py        Series list, tolerances, year ranges, sampling config
evaluator/
  evals.py            `Inspect` eval tasks, FRED tool, and within_margin scorer
  constants.py        System prompts and extract_number() response parser
tests/
  test_regex.py       Covers extract_number()
questions.json        72-question dataset (auto-generated)
aggregate_results.py  Script to print summary results tables to terminal
logs/                 Inspect .eval log files from benchmarking runs
```

## Setup

Dependencies are managed with `uv` (Python 3.13):

```bash
uv sync
```

Create a `.env` file in the repo root with:

```
FRED_API_KEY=your_fred_key        (https://fredaccount.stlouisfed.org/apikeys)
ANTHROPIC_API_KEY=your_anthropic_key
INSPECT_EVAL_MODEL=anthropic/claude-sonnet-5
```

`INSPECT_EVAL_MODEL` is the default model used when `--model` is omitted in eval runs. Local models were run through [Ollama](https://ollama.com/) (see eval commands below).

Note: `<PROIVDER>API_KEY` must match the provider used in `INSPECT_EVAL_MODEL`. This example uses Anthropic, but the structure will be generalized going forward.


## Building the dataset

Run from the repo root:

```bash
uv run python dataset/builder.py
```

This writes `questions.json` (8 series x 3 year ranges x 3 observations = 72 questions). The random seed is fixed, so re-running produces the same question set unless the config in `dataset/constants.py` changes.

## Running the evals

The current version of this eval tests two scenarios: `LLM Only` (no tools) and `LLM + FRED API` (access to one tool). See commands below to run both scenarios for the two models I tested in the initial benchmark - Sonnet 5 and Gemma 4: e4b. Any local models called must be downloaded.


**`LLM Only` - Sonnet 5**
```bash
uv run inspect eval evaluator/evals.py@closed_book_test_custom --epochs 3
```

**`LLM Only` - Gemma 4: e4b**
```bash
uv run inspect eval evaluator/evals.py@closed_book_test_custom --epochs 3 --model ollama/gemma4:e4b --temperature 1.0
```

**`LLM + FRED API` - Sonnet 5**
```bash
uv run inspect eval evaluator/evals.py@fred_api_test_custom --epochs 3 --max-connections 15
```

**`LLM + FRED API` - Gemma 4: e4b**
```bash
uv run inspect eval evaluator/evals.py@fred_api_test_custom --epochs 3 --model ollama/gemma4:e4b --temperature 1.0 --max-connections 15
```

Add `--limit 10` to any of these to run a quick test.

## Viewing results

To open the `Inspect` results dashboard, run:
```bash
uv run inspect view
```

Run the following command to see summarized results printed in the terminal. This script uses hard-coded run IDs that correspond to files in `logs/` and will need to be manually updated to work with future runs.
```bash
uv run python aggregate_results.py
```

## Development

```bash
uv run pytest
uv run ruff check && uv run ruff format
```
