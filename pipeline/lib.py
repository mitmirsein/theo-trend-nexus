import csv
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Tuple


def read_config(path: str) -> Dict[str, str]:
    cfg = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            cfg[key.strip()] = val.strip().strip('"')
    return cfg


def read_csv(path: str) -> List[Dict[str, str]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            if any((v or "").startswith("#") for v in row.values()):
                continue
            if row.get("journal_title", "").startswith("#"):
                continue
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_state(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_state(path: str, state: Dict[str, str]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def compute_date_range(cfg: Dict[str, str], mode: str, from_override: str = None, until_override: str = None) -> Tuple[str, str]:
    date_from = from_override or cfg.get("date_from")
    date_until = until_override or cfg.get("date_until")
    
    if mode == "full" or from_override:
        return date_from, date_until

    state_path = cfg.get("state_file")
    if not state_path:
        return date_from, date_until

    state = read_state(state_path)
    last_until = state.get("last_until")
    if not last_until:
        return date_from, date_until

    try:
        last_dt = datetime.strptime(last_until, "%Y-%m-%d")
    except ValueError:
        return date_from, date_until

    offset_days = int(cfg.get("incremental_offset_days", "1"))
    new_from = (last_dt + timedelta(days=offset_days)).strftime("%Y-%m-%d")
    return new_from, date_until


def update_state_range(cfg: Dict[str, str], date_from: str, date_until: str) -> None:
    state_path = cfg.get("state_file")
    if not state_path:
        return
    state = read_state(state_path)
    state.update(
        {
            "last_from": date_from,
            "last_until": date_until,
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    write_state(state_path, state)


def http_get_json(url: str, headers: Dict[str, str], retry_max: int, sleep_s: float) -> Dict:
    last_err = None
    for attempt in range(retry_max):
        try:
            print(f"DEBUG: Fetching URL: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except Exception as e:
            last_err = e
            time.sleep(sleep_s * (attempt + 1))
    raise RuntimeError(f"HTTP GET failed after {retry_max} attempts: {last_err}")


def http_get_text(url: str, headers: Dict[str, str], retry_max: int, sleep_s: float) -> str:
    last_err = None
    for attempt in range(retry_max):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            last_err = e
            time.sleep(sleep_s * (attempt + 1))
    raise RuntimeError(f"HTTP GET failed after {retry_max} attempts: {last_err}")


def write_jsonl(path: str, items: Iterable[Dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def build_query(base: str, params: Dict[str, str]) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"
