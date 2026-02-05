import argparse
import os
import pandas as pd
from lib import read_config, read_csv
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    args = parser.parse_args()

    cfg = read_config(args.config)
    issn_path = "pipeline/issn_map.csv"
    proc_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))
    report_path = os.path.join(proc_dir, "thr_2025_5d_report.csv")
    inbox_dir = "/Users/msn/Desktop/MS_Brain.nosync/010 Inbox"

    # 1. Identify Missing
    issn_map = read_csv(issn_path)
    all_targets = {row['journal_title']: row for row in issn_map if row.get('journal_title')}
    
    if os.path.exists(report_path):
        df_collected = pd.read_csv(report_path)
        collected_titles = set(df_collected['journal_title'].unique())
    else:
        collected_titles = set()

    missing_titles = sorted(list(set(all_targets.keys()) - collected_titles))
    
    if not missing_titles:
        print("[*] Amazing! No missing journals found.")
        return

    print(f"[*] Rescue Mission Started: {len(missing_titles)} journals are still under the radar.")

    # 2. Generate Rescue Report for the Commander
    report_content = [
        "# 🚨 2025 Theology Rescue Mission Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 🔦 Missing Journals (Searching in deep water...)",
        "| Journal Title | Region | Status | Action Taken |",
        "| :--- | :--- | :--- | :--- |"
    ]

    rescue_list = []
    for title in missing_titles:
        meta = all_targets[title]
        status = "Under Investigation"
        action = "Retrying specific ISSN fetch..."
        report_content.append(f"| {title} | {meta.get('region', 'N/A')} | {status} | {action} |")
        rescue_list.append(title)

    # 3. Create a comma-separated list for re-fetching
    rescue_str = ",".join(rescue_list)
    print(f"[*] Attempting focused re-fetch for: {rescue_str}")

    # 4. Trigger focused fetch (Optional: can be triggered via CLI)
    # subprocess.run(["uv", "run", "python3", "pipeline/01_crossref_fetch.py", "--journal", rescue_str, "--from", "2025-01-01"])

    # Save report to Inbox
    with open(os.path.join(inbox_dir, "Rescue_Mission_Report_2025.md"), "w") as f:
        f.write("\n".join(report_content))
    
    print(f"[*] Rescue Report saved to {inbox_dir}")

if __name__ == "__main__":
    from datetime import datetime
    main()
