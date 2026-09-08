# -*- coding: utf-8 -*-
"""전국 약수터(먹는물 공동시설) 수질검사 결과를 국립환경과학원 수질DB에서 전량 수집.

API: 기후에너지환경부 국립환경과학원_수질DB (data.go.kr id 15017324)
Base URL: apis.data.go.kr/1480523/WaterQualityService/getSgisDrinkWaterList
필수 파라미터 없음(전체 조회 가능), 지점(LEGACY_CODE_NO)당 연도·분기별로 여러 행이 쌓이는
측정로그 테이블이라 최근 3개년치를 받아 지점별로 가장 최근 검사결과 1건만 남긴다.

출력: _rawdata/list_raw_drinkwater.json - [{지점별 최신 검사결과...}, ...]
"""
import json
import os
import sys
import time
import requests
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "_rawdata" / "list_raw_drinkwater.json"

SERVICE_KEY = os.environ.get("DATA_GO_KR_API_KEY") or "9490b1d34e92aa9e25b32a4cff1438fc7b9c71e5d332413916a391e867f61e86"
BASE = "https://apis.data.go.kr/1480523/WaterQualityService/getSgisDrinkWaterList"

# 최근 3개년(당해+과거 2년) - 분기별 보고 지연을 감안해 넉넉히 잡음
YEARS = [str(date.today().year), str(date.today().year - 1), str(date.today().year - 2)]


def fetch_page(page_no, num_rows=1000, attempt=1):
    params = {
        "serviceKey": SERVICE_KEY, "pageNo": page_no, "numOfRows": num_rows,
        "resultType": "json", "yyyy": ",".join(YEARS),
    }
    try:
        r = requests.get(BASE, params=params, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        if attempt >= 3:
            print(f"  실패 page={page_no}: {e}")
            return None
        time.sleep(2)
        return fetch_page(page_no, num_rows, attempt + 1)


def main():
    all_rows = []
    page = 1
    total = None
    while True:
        data = fetch_page(page)
        if not data:
            break
        body = data.get("getSgisDrinkWaterList", {})
        items = body.get("item") or []
        if total is None:
            total = body.get("totalCount")
            print(f"전체 측정로그(최근 {len(YEARS)}개년): {total}건")
        if not items:
            break
        all_rows.extend(items)
        print(f"  {page}페이지 완료 (누적 {len(all_rows)}/{total})")
        if len(all_rows) >= (total or 0):
            break
        page += 1
        time.sleep(0.2)

    print(f"\n측정로그 총 {len(all_rows)}건 수집")

    # 지점(LEGACY_CODE_NO)별로 연도+분기가 가장 최근인 1건만 남김
    latest_by_site = {}
    for row in all_rows:
        code = row.get("LEGACY_CODE_NO")
        if not code:
            continue
        yyyy = row.get("YYYY") or "0"
        period = row.get("PERIOD") or "0/4"
        try:
            q = int(period.split("/")[0])
        except (ValueError, AttributeError):
            q = 0
        key = (int(yyyy), q)
        cur = latest_by_site.get(code)
        if cur is None or key > cur[0]:
            latest_by_site[code] = (key, row)

    rows = [v[1] for v in latest_by_site.values()]
    print(f"고유 지점 {len(rows)}개 (최신 검사결과만 채택)")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print(f"저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
