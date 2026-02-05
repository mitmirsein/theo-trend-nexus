import requests
from bs4 import BeautifulSoup
import json
import time
import os
import argparse
import random

def fetch_journal_articles(journal_name, start_year, end_year):
    url = "https://www.kci.go.kr/kciportal/po/search/poArtiSearList.kci"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.kci.go.kr/kciportal/po/search/poArtiSear.kci"
    }
    
    page_index = 1
    articles = []
    stop_fetching = False
    
    while not stop_fetching:
        print(f"  > Fetching {journal_name} page {page_index}...")
        
        params = {
            "poSearchBean.searchCurrentPage": page_index,
            "poSearchBean.docsCount": 100,
            "poSearchBean.searType": "thesis",
            "poSearchBean.conditionList": "SERE_NM",
            "poSearchBean.keywordList": journal_name,
            "poSearchBean.pubiStYr": start_year,
            "poSearchBean.pubiEndYr": end_year,
            "poSearchBean.orderType": "pubi_date_desc" # Newest first
        }
        
        try:
            resp = requests.post(url, data=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  [!] Failed to fetch page {page_index}: {resp.status_code}")
                break
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find all hidden inputs container (td)
            # We iterate over rows.
            # Look for inputs with name R_INDE_TITL
            
            # KCI table rows contain hidden inputs.
            # We can select all inputs named R_INDE_TITL, and go to parent 'td'
            title_inputs = soup.select('input[name="R_INDE_TITL"]')
            
            if not title_inputs:
                print("  [!] No articles found on this page (end of results?).")
                break
                
            count_new = 0
            
            for t_input in title_inputs:
                td = t_input.find_parent("td")
                if not td: continue
                
                # Helper to get value
                def get_val(name):
                    inp = td.find("input", {"name": name})
                    return inp.get("value", "").strip() if inp else ""

                title = get_val("R_INDE_TITL")
                author = get_val("R_CRET_NM")
                actual_journal = get_val("R_SERE_NM")
                pub_dt = get_val("R_PUBI_DT") # YYYYMM
                arti_id = get_val("R_SYST_LOCA_ID1")
                
                # Verify Year
                pub_year = pub_dt[:4] if len(pub_dt) >= 4 else "Unknown"
                
                # Stop condition: if year < start_year (and we are descending), stop
                # Be careful with "Unknown".
                if pub_year.isdigit() and int(pub_year) < int(start_year):
                    print(f"  [i] Encountered older article ({pub_year}). Stopping.")
                    stop_fetching = True
                    break
                
                # Verify Journal Name (strict-ish)
                # If searching "선교신학", accept "선교신학".
                # But sometimes it might match "한국...선교신학..".
                # User provided list is canonical.
                # If mismatch is too big, skip?
                # For now, trust the User's query logic but log the actual name.
                
                # KCI sometimes matches partial.
                # Let's save actual_journal.
                
                art_data = {
                    "journal": actual_journal, 
                    "requested_journal": journal_name,
                    "title": title,
                    "authors": [author],
                    "year": pub_year,
                    "date": pub_dt,
                    "url": f"https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId={arti_id}",
                    "arti_id": arti_id,
                    "source": "KCI_Python_Direct"
                }
                
                articles.append(art_data)
                count_new += 1
                
            print(f"  > Page {page_index}: Found {count_new} articles.")
            
            if stop_fetching:
                break
                
            if count_new < 100:
                break
            
            if page_index > 20: # Safety break (2000 articles?)
                print("  [!] Safety limit reached (20 pages). Stopping.")
                break
                
            page_index += 1
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            print(f"  [!] Error fetching page {page_index}: {e}")
            break
            
    return articles

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/raw/kci_direct_harvest.jsonl")
    args = parser.parse_args()
    
    targets = [
        "구약논단", "기독교교육논총", "기독교사회윤리", "목회와상담", "선교신학",
        "성경원문연구", "신학과 실천", "신학논단", "장신논단", "한국교회사학회지",
        "한국기독교신학논총", "한국조직신학논총", "신학사상", "신학과 철학"
    ]
    
    # Load existing if any to dedup
    unique_ids = set()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Overwrite mode for this run as it's a full refresh
    with open(args.output, 'w', encoding='utf-8') as f:
        for journal in targets:
            print(f"[*] Targeting: {journal}")
            results = fetch_journal_articles(journal, "2024", "2025") # Strict 2024-2025
            
            count = 0
            for item in results:
                if item['arti_id'] and item['arti_id'] not in unique_ids:
                    unique_ids.add(item['arti_id'])
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    count += 1
            
            print(f"[*] {journal}: Saved {count} new articles.")
            
    print(f"[*] Mission Complete. Total unique articles: {len(unique_ids)}")

if __name__ == "__main__":
    main()
