import argparse
import os
import re

from lib import read_config, ensure_dir

try:
    import pandas as pd
except ImportError as e:
    raise SystemExit("pandas is required. Install with: pip install pandas pyarrow") from e


PUNCT_RE = re.compile(r"[^a-z0-9]+")
SOURCE_RANK = {"crossref": 0, "openalex": 1, "oai": 2}


def norm_title(title: str) -> str:
    if not title:
        return ""
    t = title.lower()
    t = PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--in", dest="in_path", default="works_merged.parquet")
    parser.add_argument("--out", default="works_dedup.parquet")
    args = parser.parse_args()

    cfg = read_config(args.config)
    in_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))
    out_dir = in_dir
    ensure_dir(out_dir)

    in_path = os.path.join(in_dir, args.in_path)
    df = pd.read_parquet(in_path)

    df["title_norm"] = df["title"].fillna("").map(norm_title)
    df["source_rank"] = df["source"].map(lambda x: SOURCE_RANK.get(x, 99))

    df = df.sort_values(by=["doi", "source_rank"], na_position="last")
    df_doi = df[df["doi"].notna() & (df["doi"] != "")]
    df_nodoi = df[df["doi"].isna() | (df["doi"] == "")]

    df_doi = df_doi.drop_duplicates(subset=["doi"], keep="first")

    df_nodoi = df_nodoi.sort_values(by=["title_norm", "published_year", "journal_title", "source_rank"])
    df_nodoi = df_nodoi.drop_duplicates(subset=["title_norm", "published_year", "journal_title"], keep="first")

    out_df = pd.concat([df_doi, df_nodoi], ignore_index=True)
    out_df = out_df.drop(columns=["title_norm", "source_rank"], errors="ignore")

    out_path = os.path.join(out_dir, args.out)
    out_df.to_parquet(out_path, index=False)


if __name__ == "__main__":
    main()
