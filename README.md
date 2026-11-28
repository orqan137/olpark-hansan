# 붐빔주의보 (웹 데모)

공연과 마라톤을 피해 가는 올림픽공원 운동과 수업 시간 안내. 2026년도 공공데이터 활용 경진대회(한국체육산업개발) 출품작.

- 화면: `index.html` 한 장 (서버 없음)
- 데이터: `data.js` (아래 원자료로 자동 생성)
  - `data/parking_log.csv` 실시간 주차현황(공공데이터포털 15168686) 10분 기록
  - `data/events/m{YYYYMM}.json` 올림픽공원 공연일정(기관 누리집, 공연정보 3037877)
  - `data/hour_stats.json` 주차장 혼잡도 정보(15164156) 시간대별 기록 구성
  - `data/controls.json` 공원 주변 도로 통제(마라톤 등)
- 실시간 주차대수는 브라우저가 기관 API를 직접 호출(CORS 허용 확인)

## GitHub Pages 배포 (무료)

1. GitHub에서 새 공개 저장소를 만든다(예: `bumbim-juuibo`).
2. 이 폴더 안의 파일을 모두 올린다(`.github` 폴더 포함).
3. 저장소 Settings → Pages → Build and deployment → Source를 `Deploy from a branch`, Branch를 `main` / `(root)`로 저장.
4. Settings → Actions → General → Workflow permissions를 `Read and write permissions`로 저장.
5. Actions 탭에서 `collect` 워크플로를 한 번 `Run workflow`로 실행해 기록이 쌓이는지 확인.
6. 1~2분 뒤 `https://<계정>.github.io/bumbim-juuibo/` 주소로 접속.

`collect` 워크플로는 10분마다 주차대수 1건을 `data/parking_log.csv`에 더하고, 한 시간에 한 번 공연일정 3개월치를 갱신한 뒤 `data.js`를 다시 만든다. GitHub의 예약 실행은 몇 분 늦게 돌 수 있다.

## 직접 확인

```
python scripts/build_data.py
python -m http.server 8000
```

`http://localhost:8000/?d=2026-11-28&h=16` 처럼 날짜와 시각을 주소에 넣으면 방문 시간 판정 화면이 그 조건으로 열린다.
