import argparse
import os
import time

from lib import (
    build_query,
    compute_date_range,
    ensure_dir,
    http_get_json,
    read_config,
    read_csv,
    update_state_range,
    write_jsonl,
)


def fetch_openalex_for_issn(issn: str, cfg, out_dir: str, date_from: str, date_until: str) -> str:
    base = "https://api.openalex.org/works"
    cursor = "*"
    per_page = 200
    headers = {"User-Agent": cfg["user_agent"]}

    out_path = os.path.join(out_dir, f"openalex_{issn}.jsonl")

    while True:
        filt = ",".join(
            [
                f"locations.source.issn:{issn}",
                f"from_publication_date:{date_from}",
                f"to_publication_date:{date_until}",
            ]
        )
        params = {
            "filter": filt,
            "per-page": per_page,
            "cursor": cursor,
            "mailto": cfg.get("openalex_mailto", ""),
        }
        url = build_query(base, params)
        data = http_get_json(url, headers, int(cfg["retry_max"]), float(cfg["rate_limit_sleep"]))
        results = data.get("results", [])
        for item in results:
            item["_source"] = "openalex"

        write_jsonl(out_path, results)

        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor or len(results) == 0:
            break
        cursor = next_cursor
        time.sleep(float(cfg["rate_limit_sleep"]))

    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--issn-map", default="pipeline/issn_map.csv")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--from", dest="from_date", help="Override start date (YYYY-MM-DD)")
    parser.add_argument("--until", dest="until_date", help="Override end date (YYYY-MM-DD)")
    parser.add_argument("--journal", help="Filter by journal title or ISSN (comma-separated)")
    args = parser.parse_args()

    cfg = read_config(args.config)
    date_from, date_until = compute_date_range(cfg, args.mode, args.from_date, args.until_date)
    rows = read_csv(args.issn_map)

    target_journals = [j.strip().lower() for j in args.journal.split(",")] if args.journal else None

    out_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_raw_dir"]))
    ensure_dir(out_dir)

    print(f"[*] Starting OpenAlex fetch: {date_from} to {date_until}")

    for row in rows:
        title = row.get("journal_title", "").lower()
        issn_p = row.get("issn_print", "").strip()
        issn_o = row.get("issn_online", "").strip()

        if target_journals:
            if not any(tj in title or tj == issn_p or tj == issn_o for tj in target_journals):
                continue

        for current_issn in filter(None, [issn_p, issn_o]):
            print(f"  [+] Fetching {row.get('journal_title')} ({current_issn})...")
            count = fetch_openalex_for_issn(current_issn, cfg, out_dir, date_from, date_until)
            if isinstance(count, int) and count > 0:
                print(f"      - Found {count} items.")

    update_state_range(cfg, date_from, date_until)
    print("[*] Done.")


if __name__ == "__main__":
    main()
