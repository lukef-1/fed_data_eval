from inspect_ai.analysis import evals_df, samples_df
import pandas as pd

# Found these in a notebook using `evals_df("logs")`
EVAL_IDS = {
    "oWzumHzFzS4ojAsLjjeqyn": "sonnet_llm",
    "2NG6C7iCTb2PK7tCVFB766": "sonnet_llm_api" ,
    "mNVCg8EadPfu9BdfyqxxHU": "gemma_llm"
}

COLUMNS_TO_KEEP = ["eval_name", "id", "epoch", "input", "target", "metadata_period_full", 
                   "metadata_series_id", "metadata_series_name", "metadata_tolerance", 
                   "score_within_margin", "total_tokens", "total_time", "working_time"]

def main():
    """Load Inspect logs into a DataFrame, performing and printing basic analyses."""
    df_samples = samples_df("logs")

    df_samples["eval_name"] = df_samples["eval_id"].map(EVAL_IDS)
    df = df_samples[COLUMNS_TO_KEEP]

    df["score_quant"] = (df["score_within_margin"] == "C").astype(int)

    success_rate_overall = df.groupby("eval_name")["score_quant"].agg(mean="mean", std="std")
    success_rate_year = df.groupby(["eval_name", "metadata_period_full"])["score_quant"].agg(mean="mean", std="std")

    response_dist_overall = df.groupby("eval_name")["score_within_margin"].value_counts(normalize=True)
    response_dist_year = df.groupby(["eval_name", "metadata_period_full"])["score_within_margin"].value_counts(normalize=True)

    print("\nSuccess Rates - Overall")
    print(success_rate_overall)

    print("\nSucess Rates - By Year")
    print(success_rate_year)

    print("\nResponse Distribution - Overall")
    print(response_dist_overall)

    print("\nResponse Distribution - By Year")
    print(response_dist_year)


if __name__ == "__main__":
    main()