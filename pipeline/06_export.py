import argparse
import os

from lib import read_config, ensure_dir

try:
    import pandas as pd
except ImportError as e:
    raise SystemExit("pandas is required. Install with: pip install pandas pyarrow") from e


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--in", dest="in_path", default="works_dedup.parquet")
    args = parser.parse_args()

    cfg = read_config(args.config)
    proc_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))
    ensure_dir(proc_dir)

    in_path = os.path.join(proc_dir, args.in_path)
    df = pd.read_parquet(in_path)

    # Journal quality summary
    quality = df.groupby("journal_title").agg(
        paper_count=("title", "count"),
        abstract_rate=("abstract", lambda s: (s.notna() & (s != "")).mean()),
        doi_rate=("doi", lambda s: (s.notna() & (s != "")).mean()),
    )
    quality.to_csv(os.path.join(proc_dir, "journal_quality.csv"))

    # Yearly counts by region
    if "region" in df.columns:
        yearly = df.groupby(["published_year", "region"]).size().reset_index(name="count")
        yearly.to_csv(os.path.join(proc_dir, "yearly_region_counts.csv"), index=False)


if __name__ == "__main__":
    main()
