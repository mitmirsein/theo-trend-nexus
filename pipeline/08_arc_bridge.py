import argparse
import os
import pandas as pd
from datetime import datetime
from lib import read_config

# ARC Category Mapping Table
ARC_MAP = {
    'OT': '110', 'NT': '110',
    'Systematic Theology': '120',
    'Church History': '130',
    'Patristic': '130', 'Medieval': '130', 'Reformation': '130',
    'Ethics': '140', 'Practical Theology': '140', 'Public Theology': '140',
    'Philosophy of Religion': '410',
    'Comparative Religion': '430',
    'Method': '300'
}

def clean_filename(title):
    if not title: return "Unknown"
    title = str(title)
    keepcharacters = (' ', '.', '_', '-')
    return "".join(c for c in title if c.isalnum() or c in keepcharacters).rstrip()[:100]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--in", dest="in_path", default="thr_2025_5d_report.csv")
    args = parser.parse_args()

    cfg = read_config(args.config)
    issn_path = "pipeline/issn_map.csv"
    from lib import read_csv
    issn_map = read_csv(issn_path)

    
    proc_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))

    inbox_dir = "/Users/msn/Desktop/MS_Brain.nosync/010 Inbox/2025_Journal_Digests"
    if not os.path.exists(inbox_dir):
        os.makedirs(inbox_dir, exist_ok=True)

    
    # Load analyzed report
    input_file = os.path.join(proc_dir, args.in_path)
    if not os.path.exists(input_file):
        print(f"[!] Input file not found: {input_file}")
        return
    df_all = pd.read_csv(input_file)
    
    # Group by Journal to create separate digests
    journals_in_dataset = df_all.groupby('journal_title')
    
    # Get target list for filtering
    target_titles = set(row.get('journal_title') for row in issn_map if row.get('journal_title'))
    
    print(f"[*] Found {len(journals_in_dataset)} potential journals. Filtering for target 88 journals...")

    generated_count = 0
    for journal_name, df in journals_in_dataset:
        # Strict Filtering: Only allow journals that exist in our target_titles list
        if not journal_name or journal_name not in target_titles:
            continue
        
        if df.empty:
            continue

        generated_count += 1

        year = df.iloc[0]['published_year']
        safe_journal_name = clean_filename(journal_name)
        filename = f"Journal_Digest_{safe_journal_name}_{year}.md"
        file_path = os.path.join(inbox_dir, filename)

        # Build Header
        content = [
            "---",
            f"title: \"{journal_name} ({year}) Digest\"",
            f"tags: [Theology/Digest, Trend/{year}, Journal/{journal_name}]",
            f"created: {datetime.now().strftime('%Y-%m-%d')}",
            "category: '600'",
            "arc_score: 6",
            "---",
            f"# 🦅 {journal_name} ({year}) Theological Digest",
            "",
            "> [!INFO] Intelligence Summary",
            f"> 본 보고서는 **theo-trend-nexus** 5D 분석 엔진을 통해 생성된 {journal_name} 저널의 {year}년호 요약입니다.",
            "",
            "## 📊 Content Table",
            "| No | Subfield | Era | Title |",
            "| :--- | :--- | :--- | :--- |"
        ]

        # Reset index for display numbering
        df_reset = df.reset_index(drop=True)

        # Build Table rows
        for i, row in df_reset.iterrows():
            sub = str(row.get('subfield_tags', '')).replace(";", ", ")
            era = str(row.get('era_tags', '')).replace(";", ", ")
            title = str(row.get('title', 'Unknown Title'))
            content.append(f"| {i+1} | {sub} | {era} | [[#{clean_filename(title)}]] |")

        content.append("\n---\n")

        # Build Individual Entries
        for i, row in df_reset.iterrows():
            title = str(row.get('title', 'Unknown Title'))
            content.append(f"### {clean_filename(title)}")
            content.append(f"- **DOI**: {row.get('doi', 'N/A')}")
            content.append(f"- **Analytical Tags**: `{row.get('subfield_tags', '')} / {row.get('method_tags', '')} / {row.get('era_tags', '')}`")
            content.append(f"- **Abstract**: {row.get('abstract', 'No abstract available')}")
            content.append("\n---\n")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            # print(f"[*] Created: {filename}")
        except Exception as e:
            print(f"[Error] Failed to create {filename}: {e}")

    print(f"[*] Success! All digests have been transported to: {inbox_dir}")

if __name__ == "__main__":
    main()
