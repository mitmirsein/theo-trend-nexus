import argparse
import os
import time
import xml.etree.ElementTree as ET

from lib import (
    build_query,
    compute_date_range,
    ensure_dir,
    http_get_text,
    read_config,
    read_csv,
    update_state_range,
    write_jsonl,
)


NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def parse_oai_xml(xml_text: str, journal_title: str):
    root = ET.fromstring(xml_text)
    records = []

    for rec in root.findall(".//oai:record", NS):
        metadata = rec.find("oai:metadata", NS)
        if metadata is None:
            continue
        dc = metadata.find(".//dc:dc", NS)
        if dc is None:
            continue
        def texts(tag):
            return [el.text.strip() for el in dc.findall(f"dc:{tag}", NS) if el.text]

        record = {
            "title": texts("title"),
            "identifier": texts("identifier"),
            "creator": texts("creator"),
            "subject": texts("subject"),
            "publisher": texts("publisher"),
            "date": texts("date"),
            "source": texts("source"),
            "language": texts("language"),
            "type": texts("type"),
            "description": texts("description"),
            "journal_title": journal_title,
            "_source": "oai-pmh",
        }
        records.append(record)

    token_el = root.find(".//oai:resumptionToken", NS)
    token = token_el.text.strip() if token_el is not None and token_el.text else None
    return records, token


def harvest(endpoint: str, prefix: str, cfg, journal_title: str, out_dir: str, date_from: str, date_until: str):
    token = None
    headers = {"User-Agent": cfg["user_agent"]}
    out_path = os.path.join(out_dir, f"oai_{journal_title.replace(' ', '_')}.jsonl")

    while True:
        if token:
            params = {"verb": "ListRecords", "resumptionToken": token}
        else:
            params = {
                "verb": "ListRecords",
                "metadataPrefix": prefix,
                "from": date_from,
                "until": date_until,
            }
        url = build_query(endpoint, params)
        xml_text = http_get_text(url, headers, int(cfg["retry_max"]), float(cfg["rate_limit_sleep"]))
        records, token = parse_oai_xml(xml_text, journal_title)
        write_jsonl(out_path, records)

        if not token:
            break
        time.sleep(float(cfg["rate_limit_sleep"]))

    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--oai-endpoints", default="pipeline/oai_endpoints.csv")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument("--from", dest="from_date", help="Override start date (YYYY-MM-DD)")
    parser.add_argument("--until", dest="until_date", help="Override end date (YYYY-MM-DD)")
    parser.add_argument("--journal", help="Filter by journal title (comma-separated)")
    args = parser.parse_args()

    cfg = read_config(args.config)
    date_from, date_until = compute_date_range(cfg, args.mode, args.from_date, args.until_date)
    rows = read_csv(args.oai_endpoints)

    target_journals = [j.strip().lower() for j in args.journal.split(",")] if args.journal else None

    out_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_raw_dir"]))
    ensure_dir(out_dir)

    for row in rows:
        title = row.get("journal_title")
        if not title:
            continue
        
        if target_journals:
            if not any(tj in title.lower() for tj in target_journals):
                continue

        endpoint = row.get("oai_endpoint")
        prefix = row.get("metadata_prefix") or "oai_dc"
        if not title or not endpoint:
            continue
        out_path = os.path.join(out_dir, f"oai_{title.replace(' ', '_')}.jsonl")
        if args.skip_existing and os.path.exists(out_path):
            continue
        harvest(endpoint, prefix, cfg, title, out_dir, date_from, date_until)

    update_state_range(cfg, date_from, date_until)


if __name__ == "__main__":
    main()
