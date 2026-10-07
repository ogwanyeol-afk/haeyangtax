# 세무 뉴스 자동 수집: 구글 뉴스 RSS(제목·언론사·링크만) → news.json
import json, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

QUERIES = [
    "세무 OR 세법 OR 국세청 when:3d",
    "종합소득세 OR 부가가치세 OR 법인세 when:3d",
    "상속세 OR 증여세 OR 양도소득세 when:3d",
    "조세심판원 OR 조세 판결 when:7d",
    "세법개정 OR 세액공제 OR 세액감면 when:7d",
]
# 세무 전문지 우선 표시
PRIORITY = ["조세일보", "세정일보", "택스워치", "TAXWATCH", "日刊 NTN", "일간NTN", "세무사신문", "한국세정신문", "택스타임즈", "조세금융신문"]
KEEP = 40
KST = timezone(timedelta(hours=9))

def fetch(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (haeyangtax.com news bot)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(" - " + src)]
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            continue
        out.append({"title": title, "source": src, "url": (it.findtext("link") or "").strip(), "date": dt.strftime("%Y-%m-%d %H:%M")})
    return out

def main():
    items, seen = [], set()
    for q in QUERIES:
        try:
            got = parse(fetch(q))
        except Exception as e:
            print("skip", q, e); continue
        for x in got:
            key = re.sub(r"\W", "", x["title"])[:40]
            if key and key not in seen and x["url"]:
                seen.add(key); items.append(x)
    if not items:
        print("no items; keep old news.json"); return
    cutoff = (datetime.now(KST) - timedelta(days=7)).strftime("%Y-%m-%d")
    items = [x for x in items if x["date"] >= cutoff]
    items.sort(key=lambda x: x["date"], reverse=True)
    pri = [x for x in items if any(p in x["source"] for p in PRIORITY)]
    rest = [x for x in items if x not in pri]
    items = sorted((pri[:25] + rest)[:KEEP], key=lambda x: x["date"], reverse=True)
    data = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), "items": items}
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("saved", len(items))

if __name__ == "__main__":
    main()
