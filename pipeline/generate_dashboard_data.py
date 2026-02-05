import pandas as pd
import json
import os

def generate_stats():
    csv_path = "/Users/msn/Desktop/MS_Dev.nosync/projects/theo-trend-nexus/data/processed/thr_2025_5d_report.csv"
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    # 저널 다이제스트 스캔 (MS_Brain 연계)
    digest_dir = "/Users/msn/Desktop/MS_Brain.nosync/010 Inbox/2025_Journal_Digests"
    journal_digests = {}
    if os.path.exists(digest_dir):
        for filename in os.listdir(digest_dir):
            if filename.startswith("Journal_Digest_") and filename.endswith(".md"):
                # Journal_Digest_NAME_2025.md -> NAME
                parts = filename.replace("Journal_Digest_", "").replace(".md", "").split("_")
                journal_name = "_".join(parts[:-1]) if len(parts) > 1 else parts[0]
                journal_digests[journal_name] = filename

    df = pd.read_csv(csv_path)
    
    # NaN 값을 빈 문자열이나 0으로 치환
    df = df.fillna("")
    
    import re
    def contains_hangul(text):
        return bool(re.search('[가-힣]', str(text)))

    # 언어(region) 복구 작전: 미분류 데이터를 제목 기반으로 재배치
    def recover_language(row):
        reg = str(row['region']).strip()
        if reg == 'unknown' or not reg:
            if contains_hangul(row['title']):
                return 'ko'
            else:
                return 'en' # 기본적으로 라틴 문자면 영어군으로 배속
        return reg

    df['region'] = df.apply(recover_language, axis=1)
    
    # 저널 리스트 정제 (빈 값 제거)
    journal_titles = [j.strip() for j in df['journal_title'].unique() if j and str(j).strip()]
    journal_titles.sort()

    def aggregate_multi_tags(series):
        all_tags = []
        for tags in series:
            if not tags or tags == "Unclassified" or tags == "General" or tags == "Modern/General":
                continue
            # 세미콜론으로 구분된 태그들을 분리하여 리스트에 추가
            split_tags = [t.strip() for t in str(tags).split(';') if t.strip()]
            all_tags.extend(split_tags)
        
        from collections import Counter
        return dict(Counter(all_tags).most_common(12))

    # 기초 통계 생성
    subfields_raw = aggregate_multi_tags(df['subfield_tags'])
    
    # 학계 표준 순서 정의
    academic_order = [
        "OT", "NT", "Church History", "Systematic Theology", 
        "Ethics", "Philosophy/Ethics", "Practical Theology", 
        "Mission", "Missiology", "World Christianity"
    ]
    
    # 표준 순서에 따라 정렬하되, 리스트에 없는 항목은 뒤에 배치
    sorted_subfields = {}
    for key in academic_order:
        if key in subfields_raw:
            sorted_subfields[key] = subfields_raw.pop(key)
    
    # 나머지 항목들 추가
    sorted_subfields.update(subfields_raw)

    # 시대별 표준 순서 정의 (연대순)
    era_order = [
        "Patristic", "Medieval", "Reformation", "Modern", "Contemporary"
    ]
    
    eras_raw = aggregate_multi_tags(df['era_tags'])
    sorted_eras = {}
    for key in era_order:
        if key in eras_raw:
            sorted_eras[key] = eras_raw.pop(key)
    sorted_eras.update(eras_raw)

    # 최근 획득 논문 (이중 언어 처리용)
    recent_raw = df[['title', 'journal_title', 'published_year', 'subfield_tags', 'method_tags', 'era_tags', 'source']].head(10).to_dict(orient='records')
    
    # 번역 맵 (데모용)
    translation_map = {
        "Digital Blackface and Its Argumentative Implications": "디지털 블랙페이스와 그 논증적 함의",
        "Doing Away with Skepticism about Harm": "해악에 대한 회의론 없애기",
        "Conceptual Mediation in Technomoral Change: Reply to Danaher and Sætra": "기술도덕적 변화에서의 개념적 매개: 대나허와 세트라에 대한 답변",
        "Diachronic or Counterfactual? Temporal Well-Being and Changing Attitudes": "통시적인가, 반사실적인가? 시간적 웰빙과 변화하는 태도",
        "Fitting Love and Uniqueness": "적실한 사랑과 고유성",
        "A Value-Free, Diversity-Sensitive Measure of Freedom": "가치 중립적이고 다양성에 민감한 자유의 척도",
        "Thinking Functionally About Moral Assertion": "도덕적 단언에 대해 기능적으로 생각하기",
    }
    
    recent_articles = []
    for art in recent_raw:
        title = art['title']
        if art['source'] == 'kci':
            # KCI는 한글이 기본
            art['title_ko'] = title
            art['title_en'] = "English translation pending..." # 실제 데이터에 있으면 추출
        else:
            # Crossref 등은 영어가 기본
            art['title_en'] = title
            art['title_ko'] = translation_map.get(title, "한글 번역 준비 중...")
        recent_articles.append(art)

    # 교파별 통계 정제 (신학적 전통 우선)
    canonical_confessions = ["Catholic", "Protestant", "Reformed", "Anglican", "Ecumenical", "Evangelical", "Lutheran", "Methodist"]
    confessions_raw = df['confession'].value_counts().to_dict()
    
    # 제외할 용어 (학문적 분류나 미분류)
    exclude_confessions = ["Academic", "unknown", "History", "Practical", "Science", "Mission", "Political", "Ethics", "Spirituality", "Philosophy/Ethics"]
    
    filtered_confessions = {}
    # 1. 정석 교파들 먼저 체크
    for conf in canonical_confessions:
        if conf in confessions_raw:
            filtered_confessions[conf] = confessions_raw.pop(conf)
    
    # 2. 나머지는 비중 순으로 추가 (제외 용어 빼고)
    remaining = {k: v for k, v in confessions_raw.items() if k not in exclude_confessions}
    sorted_remaining = dict(sorted(remaining.items(), key=lambda x: x[1], reverse=True))
    filtered_confessions.update(sorted_remaining)


    stats = {
        "total_articles": int(len(df)),
        "total_journals": len(journal_titles),
        "journal_list": journal_titles,
        "sources": df['source'].value_counts().to_dict(),
        "subfields": sorted_subfields,
        "methods": aggregate_multi_tags(df['method_tags']),
        "eras": sorted_eras,
        "regions": df['region'].value_counts().head(10).to_dict(),
        "confessions": dict(list(filtered_confessions.items())[:10]),
        "years": df['published_year'].value_counts().sort_index().to_dict(),
        "recent_articles": recent_articles,
        "journal_digests": journal_digests
    }

    output_dir = "/Users/msn/Desktop/MS_Dev.nosync/projects/theo-trend-nexus/dashboard/src/data"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("Stats generated successfully!")

if __name__ == "__main__":
    generate_stats()
