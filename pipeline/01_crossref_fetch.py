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


def fetch_crossref_for_issn(issn: str, cfg, out_dir: str, date_from: str, date_until: str) -> int:
    base = "https://api.crossref.org/works"
    cursor = "*"
    rows_per_page = 1000
    headers = {"User-Agent": cfg["user_agent"]}
    total_found = 0

    out_path = os.path.join(out_dir, f"crossref_{issn}.jsonl")
    
    # Check if already fetched in this session to avoid duplicates if print/online are same
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return 0

    while True:
        params = {
            "filter": f"issn:{issn},from-pub-date:{date_from},until-pub-date:{date_until},type:journal-article",
            "cursor": cursor,
            "rows": rows_per_page,
        }
        url = build_query(base, params)
        try:
            data = http_get_json(url, headers, int(cfg["retry_max"]), float(cfg["rate_limit_sleep"]))
        except Exception as e:
            print(f"  [Error] Failed to fetch ISSN {issn}: {e}")
            break
            
        message = data.get("message", {})
        items = message.get("items", [])

        for item in items:
            item["_source"] = "crossref"
            item["_target_issn"] = issn

        write_jsonl(out_path, items)
        total_found += len(items)

        next_cursor = message.get("next-cursor")
        if not next_cursor or len(items) == 0:
            break
        cursor = next_cursor
        time.sleep(float(cfg["rate_limit_sleep"]))

    return total_found


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

    print(f"[*] Starting Crossref fetch: {date_from} to {date_until}")

    for row in rows:
        title = row.get("journal_title", "").lower()
        issn_p = row.get("issn_print", "").strip()
        issn_o = row.get("issn_online", "").strip()

        if target_journals:
            if not any(tj in title or tj == issn_p or tj == issn_o for tj in target_journals):
                continue

        # Try both ISSNs
        for current_issn in filter(None, [issn_p, issn_o]):
            print(f"  [+] Fetching {row.get('journal_title')} ({current_issn})...")
            count = fetch_crossref_for_issn(current_issn, cfg, out_dir, date_from, date_until)
            if count > 0:
                print(f"      - Found {count} items.")

    update_state_range(cfg, date_from, date_until)
    print("[*] Done.")


if __name__ == "__main__":
    main()
