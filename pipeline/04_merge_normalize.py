import argparse
import glob
import json
import os
import re

from lib import read_config, ensure_dir

try:
    import pandas as pd
except ImportError as e:
    raise SystemExit("pandas is required. Install with: pip install pandas pyarrow") from e


DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def read_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def abstract_from_inverted_index(inv):
    if not inv:
        return None
    tokens = []
    # inv: {token: [positions]}
    for token, positions in inv.items():
        for pos in positions:
            tokens.append((pos, token))
    tokens.sort(key=lambda x: x[0])
    return " ".join(tok for _, tok in tokens)


def extract_doi(text_list):
    for t in text_list or []:
        if not t:
            continue
        m = DOI_RE.search(t)
        if m:
            return m.group(0).lower()
    return None


def normalize_crossref(item):
    doi = (item.get("DOI") or "").lower() or None
    title = (item.get("title") or [None])[0]
    abstract = item.get("abstract")
    issued = item.get("issued", {}).get("date-parts", [[None]])[0]
    year = issued[0] if issued else None
    journal_title = (item.get("container-title") or [None])[0]
    issn_list = item.get("ISSN") or []
    publisher = item.get("publisher")
    authors = []
    for a in item.get("author") or []:
        name = " ".join([a.get("given", ""), a.get("family", "")]).strip()
        if name:
            authors.append(name)
    subject = item.get("subject") or []
    ref_count = item.get("is-referenced-by-count") or item.get("reference-count")

    return {
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "published_year": year,
        "journal_title": journal_title,
        "issn_list": issn_list,
        "publisher": publisher,
        "authors": authors,
        "subject": subject,
        "ref_count": ref_count,
        "source": "crossref",
    }


def normalize_openalex(item):
    doi = (item.get("doi") or "").replace("https://doi.org/", "").lower() or None
    title = item.get("title")
    abstract = abstract_from_inverted_index(item.get("abstract_inverted_index"))
    year = item.get("publication_year")
    journal_title = (item.get("host_venue") or {}).get("display_name")
    issn_list = (item.get("host_venue") or {}).get("issn") or []
    publisher = (item.get("host_venue") or {}).get("publisher")
    authors = []
    for a in item.get("authorships") or []:
        name = (a.get("author") or {}).get("display_name")
        if name:
            authors.append(name)
    subject = [k.get("display_name") for k in (item.get("keywords") or []) if k.get("display_name")]
    ref_count = item.get("cited_by_count")

    return {
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "published_year": year,
        "journal_title": journal_title,
        "issn_list": issn_list,
        "publisher": publisher,
        "authors": authors,
        "subject": subject,
        "ref_count": ref_count,
        "source": "openalex",
    }


def normalize_oai(item):
    title = (item.get("title") or [None])[0]
    date_list = item.get("date") or []
    year = None
    for d in date_list:
        if d and len(d) >= 4 and d[:4].isdigit():
            year = int(d[:4])
            break
    identifiers = item.get("identifier") or []
    doi = extract_doi(identifiers)
    publisher = (item.get("publisher") or [None])[0]
    authors = item.get("creator") or []
    subject = item.get("subject") or []

    return {
        "doi": doi,
        "title": title,
        "abstract": (item.get("description") or [None])[0],
        "published_year": year,
        "journal_title": item.get("journal_title"),
        "issn_list": [],
        "publisher": publisher,
        "authors": authors,
        "subject": subject,
        "ref_count": None,
        "source": "oai",
    }



def normalize_kci(item):
    # KCI scraper provides 'arti_id' and sometimes 'doi'.
    # We use 'arti_id' as a fallback identifier if DOI is missing.
    doi = (item.get("doi") or item.get("arti_id") or "").lower()
    if not doi:
        doi = None
    
    # Title
    title = item.get("title")
    
    # Abstract
    abstract = item.get("abstract")
    
    # Year
    year = item.get("year")
    if year and str(year).isdigit():
        year = int(year)
    else:
        year = None
        
    # Journal
    journal_title = item.get("journal")
    
    # Authors
    authors = item.get("authors") or []
    
    return {
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "published_year": year,
        "journal_title": journal_title,
        "issn_list": [], # No ISSN from scraper yet
        "publisher": "KCI",
        "authors": authors,
        "subject": [],
        "ref_count": None,
        "source": "kci",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--raw-dir", default=None)
    parser.add_argument("--out", default="works_merged.parquet")
    args = parser.parse_args()

    cfg = read_config(args.config)
    raw_dir = args.raw_dir or os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_raw_dir"]))
    out_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))
    ensure_dir(out_dir)

    records = []

    for path in glob.glob(os.path.join(raw_dir, "crossref_*.jsonl")):
        for item in read_jsonl(path):
            records.append(normalize_crossref(item))

    for path in glob.glob(os.path.join(raw_dir, "openalex_*.jsonl")):
        for item in read_jsonl(path):
            records.append(normalize_openalex(item))

    for path in glob.glob(os.path.join(raw_dir, "oai_*.jsonl")):
        for item in read_jsonl(path):
            records.append(normalize_oai(item))

    for path in glob.glob(os.path.join(raw_dir, "kci_*.jsonl")):
        for item in read_jsonl(path):
            records.append(normalize_kci(item))

    df = pd.DataFrame(records)
    out_path = os.path.join(out_dir, args.out)
    df.to_parquet(out_path, index=False)


if __name__ == "__main__":
    main()
