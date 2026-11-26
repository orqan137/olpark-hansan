"""data/ 폴더의 원자료로 화면용 data.js 생성.

- data/events/m{YYYYMM}.json : 올림픽공원 공연일정 월별 목록(기관 누리집 eventInfoListAjax 응답 그대로)
- data/parking_log.csv       : 실시간 주차현황 API 10분 기록(ts_kst,parking_sum)
- data/hour_stats.json       : 주차장 혼잡도 정보(15164156) 시간대별 기록 구성
- data/controls.json         : 공원 주변 도로 통제(마라톤 등) 일정
"""
import csv, datetime as T, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
BIG = ("KSPO", "체조", "핸드볼", "티켓링크", "88잔디")
WD = "월화수목금토일"
WD_EN = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def venue(p):
    p = p.replace(" ", "")
    if "KSPO" in p or "체조" in p: return "KSPO DOME"
    if "핸드볼" in p or "티켓링크" in p: return "핸드볼경기장"
    if "88잔디" in p: return "88잔디마당"
    if "올림픽홀" in p: return "올림픽홀"
    if "우리금융" in p: return "우리금융아트홀"
    if "뮤즈" in p: return "뮤즈라이브"
    return "기타"


def hour_of(chunk):
    m = re.search(r"(오전|오후)?\s*(\d{1,2})\s*(?::(\d{2}))?\s*(시|PM|pm|AM|am|:)", chunk)
    if not m:
        m = re.search(r"(오전|오후)?\s*(\d{1,2}):(\d{2})()", chunk)
    if not m:
        return None
    h = int(m.group(2)); mm = int(m.group(3) or 0)
    if m.group(4) == "시":
        bun = re.match(r"\s*(\d{1,2})\s*분", chunk[m.end():])
        if bun: mm = int(bun.group(1))
    pm = (m.group(1) == "오후") or (m.group(4) or "").lower() == "pm"
    if pm and h < 12: h += 12
    if not m.group(1) and not (m.group(4) or "").lower() in ("pm", "am") and h < 9: h += 12  # '6시' 같은 표기는 저녁 공연
    if h > 23: return None
    return f"{h:02d}:{mm:02d}"


def start_times(tm, days):
    """공연 시간 안내 문장에서 날짜별 시작 시각 추출. 못 찾으면 None."""
    tm = (tm or "").replace("（", "(").replace("）", ")")
    chunks = re.split(r"/|\n|(?=\d{4}년)|(?=\d{1,2}월\s*\d{1,2}일)|(?=\d{4}\.\d{1,2}\.\d{1,2})|(?=\b\d{1,2}\.\d{1,2}\s*\()", tm)
    by_date, by_wd, any_t = {}, {}, None
    for c in chunks:
        t = hour_of(re.sub(r"\d{4}[년.]\s*|\d{1,2}\s*[월.]\s*\d{1,2}\s*일?\.?", " ", c))
        if not t: continue
        any_t = any_t or t
        md = re.search(r"(\d{1,2})\s*[월.]\s*(\d{1,2})", c)
        if md:
            by_date[(int(md.group(1)), int(md.group(2)))] = t
        for w in re.findall(r"[(\s]?([월화수목금토일])(?:요일)?[)\s,]", " " + c + " "):
            by_wd.setdefault(WD.index(w), t)
        for w in re.findall(r"\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b", c.upper()):
            by_wd.setdefault(WD_EN[w], t)
    out = {}
    for d in days:
        out[d.isoformat()] = by_date.get((d.month, d.day)) or by_wd.get(d.weekday()) or (any_t if len(by_date) <= 1 and not by_wd else None)
    return out, bool(by_date)


def build_events():
    ev = {}
    for f in sorted(glob.glob(os.path.join(D, "events", "m*.json"))):
        for grp in json.load(open(f, encoding="utf-8")):
            for it in grp or []:
                ev[it["evtSeq"]] = it
    days = {}
    for it in ev.values():
        try:
            b = T.date.fromisoformat(str(it["beginDt"])[:10]); e = T.date.fromisoformat(str(it["endDt"])[:10])
        except ValueError:
            continue
        if (e - b).days > 40:
            continue
        span = [b + T.timedelta(days=i) for i in range((e - b).days + 1)]
        st, explicit = start_times(it.get("tm"), span)
        if explicit and len(span) > 2:
            span = [d for d in span if st.get(d.isoformat())]
        v = venue(it.get("plc") or "")
        for d in span:
            days.setdefault(d.isoformat(), []).append({
                "venue": v, "big": any(k in (it.get("plc") or "").replace(" ", "") for k in BIG),
                "title": re.sub(r"\s+", " ", it["title"]).strip(), "start": st.get(d.isoformat()),
                "url": f"https://www.ksponco.or.kr/olympicpark/eventInfo/eventInfoView.es?mid=a20301010100&evtSeq={it['evtSeq']}"})
    for v in days.values():
        v.sort(key=lambda x: (not x["big"], x["start"] or "99"))
    return days


def build_parking():
    rows = []
    with open(os.path.join(D, "parking_log.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["parking_sum"].isdigit():
                rows.append([r["ts_kst"], int(r["parking_sum"])])
    return rows


def main():
    data = {
        "built": (T.datetime.now(T.timezone.utc) + T.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M"),
        "events": build_events(),
        "parking": build_parking(),
        "hours": json.load(open(os.path.join(D, "hour_stats.json"), encoding="utf-8")),
        "controls": json.load(open(os.path.join(D, "controls.json"), encoding="utf-8")),
    }
    with open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.OLPARK = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("events days", len(data["events"]), "parking rows", len(data["parking"]))


if __name__ == "__main__":
    main()
