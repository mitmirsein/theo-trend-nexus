import argparse
import os
import json
import pandas as pd
from lib import read_config, read_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="pipeline/config.yaml")
    parser.add_argument("--in", dest="in_path", default="works_dedup.parquet")
    args = parser.parse_args()

    cfg = read_config(args.config)
    proc_dir = os.path.abspath(os.path.join(os.path.dirname(args.config), cfg["output_processed_dir"]))
    # Lexicon is in the root, not inside pipeline/
    lex_path = os.path.abspath(os.path.join(os.path.dirname(args.config), "../subfield_method_lexicon.csv"))
    issn_path = os.path.join(os.path.dirname(args.config), "issn_map.csv")

    # Load Data
    df = pd.read_parquet(os.path.join(proc_dir, args.in_path))
    lexicon = read_csv(lex_path)
    issn_map = read_csv(issn_path)

    # Prepare ISSN-based metadata mapping with normalization
    def normalize_issn(issn):
        return str(issn).replace("-", "").strip().upper()

    issn_to_meta = {}
    title_to_meta = {}
    for row in issn_map:
        p_issn = normalize_issn(row.get('issn_print', ''))
        o_issn = normalize_issn(row.get('issn_online', ''))
        j_title = row.get('journal_title')
        
        if p_issn: issn_to_meta[p_issn] = row
        if o_issn: issn_to_meta[o_issn] = row
        if j_title: title_to_meta[j_title.strip().lower()] = row

    # Canonicalize Journal Titles and Add Metadata via ISSN matching
    def canonicalize_and_meta(row):
        issns = [normalize_issn(i) for i in row.get('issn_list', [])]
        for issn in issns:
            if issn in issn_to_meta:
                meta = issn_to_meta[issn]
                return pd.Series([
                    meta.get('journal_title', row.get('journal_title')), # Canonical Title
                    meta.get('region', 'unknown'), 
                    meta.get('confession', 'unknown')
                ])
                
        # Fallback: Title Match
        j_title_raw = row.get('journal_title')
        if j_title_raw:
            j_title_norm = j_title_raw.strip().lower()
            if j_title_norm in title_to_meta:
                meta = title_to_meta[j_title_norm]
                return pd.Series([
                    meta.get('journal_title', j_title_raw),
                    meta.get('region', 'unknown'),
                    meta.get('confession', 'unknown')
                ])
                
        return pd.Series([row.get('journal_title'), 'unknown', 'unknown'])

    print("[*] Canonicalizing journal titles with Ultra-Precise ISSN matching...")
    df[['journal_title', 'region', 'confession']] = df.apply(canonicalize_and_meta, axis=1)

    # Keyword Matching Engine
    def tag_dimensions(row):
        text = f"{row.get('title', '')} {row.get('abstract', '')}".lower()
        tags = {
            'subfields': set(),
            'methods': set(),
            'eras': set()
        }
        for entry in lexicon:
            cat = entry['category']
            type_name = entry['type']
            terms = [t.strip() for t in entry['terms'].split(';') if t.strip()]
            
            if any(term in text for term in terms):
                if cat == 'subfield': tags['subfields'].add(type_name)
                elif cat == 'method': tags['methods'].add(type_name)
                elif cat == 'era': tags['eras'].add(type_name)
        
        return pd.Series([
            ";".join(sorted(tags['subfields'])),
            ";".join(sorted(tags['methods'])),
            ";".join(sorted(tags['eras']))
        ])

    print("[*] Applying 5D analysis engine...")
    df[['subfield_tags', 'method_tags', 'era_tags']] = df.apply(tag_dimensions, axis=1)

    # Summary Report
    print("\n=== 🏛️ 5D Theology Trend Report (ThR 2025) ===\n")
    
    print("1. [Subfields] 집중 분야")
    print(df['subfield_tags'].str.split(';').explode().value_counts().drop('', errors='ignore').head(5))
    
    print("\n2. [Methods] 분석 방법론")
    print(df['method_tags'].str.split(';').explode().value_counts().drop('', errors='ignore').head(5))
    
    print("\n3. [Eras] 조명된 시대")
    print(df['era_tags'].str.split(';').explode().value_counts().drop('', errors='ignore').head(5))
    
    print("\n4. [Contexts] 지역 및 전통")
    print(f"Region: {df['region'].unique()}")
    print(f"Confession: {df['confession'].unique()}")

    # Save detailed report
    out_path = os.path.join(proc_dir, "thr_2025_5d_report.csv")
    df.to_csv(out_path, index=False)
    print(f"\n[*] Detailed report saved to: {out_path}")

if __name__ == "__main__":
    main()
