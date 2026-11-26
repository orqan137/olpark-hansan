"""GitHub Actions에서 10분마다 실행: 실시간 주차 1건 기록, 공연일정(이번 달부터 3개월) 갱신, data.js 재생성."""
import datetime as T, json, os, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
PARKING = "https://www.ksponco.or.kr/online/main/parkingorsApi.do?apiKey=PARKING21803504"  # 기관이 공개한 키
EVENTS = "https://www.ksponco.or.kr/olympicpark/eventInfo/eventInfoListAjax.es"
now = T.datetime.now(T.timezone.utc) + T.timedelta(hours=9)


def get(url, body=None):
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "olpark-hansan/1.0", **({"Content-Type": "application/json;charset=UTF-8"} if body else {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


try:
    v = json.loads(get(PARKING))[0]["parking_sum"]
except Exception as e:  # 실패해도 기록은 남김
    print("parking error", e); v = "NA"
log = os.path.join(D, "parking_log.csv")
if not os.path.exists(log):
    open(log, "w", encoding="utf-8").write("ts_kst,parking_sum\n")
open(log, "a", encoding="utf-8").write(f"{now:%Y-%m-%dT%H:%M},{v}\n")

if now.minute < 10:  # 공연일정은 한 시간에 한 번만 갱신
    os.makedirs(os.path.join(D, "events"), exist_ok=True)
    for k in range(3):
        y, m = now.year + (now.month - 1 + k) // 12, (now.month - 1 + k) % 12 + 1
        ym = f"{y}{m:02d}"
        try:
            body = get(EVENTS, json.dumps({"nowYM": ym, "plcCd": ""}).encode())
            json.loads(body)
            open(os.path.join(D, "events", f"m{ym}.json"), "w", encoding="utf-8").write(body)
        except Exception as e:
            print("events error", ym, e)

subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_data.py")], check=True)
