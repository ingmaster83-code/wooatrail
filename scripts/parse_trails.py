#!/usr/bin/env python3
"""
parse_trails.py - 전국길관광정보표준데이터 원본 JSON을 사이트용 _rawdata/trails.json으로 변환

사용법:
  python scripts/parse_trails.py
"""
import sys, json, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
SRC = ROOT / "mountain" / "전국길관광정보표준데이터.json"
OUT = ROOT / "_rawdata" / "trails.json"

SIDO_ALIAS = {
    "강원도": "강원특별자치도",
    "전라북도": "전북특별자치도",
}


def slugify(name: str, idx: int) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", name).strip("-")
    return f"{idx}-{s}"


def parse_sido_sigungu(addr: str):
    if not addr:
        return "", ""
    parts = addr.strip().split()
    if not parts:
        return "", ""
    sido = SIDO_ALIAS.get(parts[0], parts[0])
    sigungu = parts[1] if len(parts) > 1 else ""
    return sido, sigungu


def parse_distance(v: str):
    if not v:
        return 0.0
    m = re.search(r"[\d.]+", str(v))
    return float(m.group()) if m else 0.0


def parse_minutes(s: str):
    """소요시간 문자열에서 분 단위 숫자를 최대한 파싱. 애매하면 None(스킵)."""
    if not s:
        return None
    s = s.strip()
    m = re.match(r"^(\d+)\s*일", s)
    if m:
        return int(m.group(1)) * 1440
    m = re.match(r"^(\d+)\s*시간\s*(\d+)?\s*분?", s)
    if m:
        h = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        return h * 60 + mm
    m = re.match(r"^(\d+)\s*분$", s)
    if m:
        return int(m.group(1))
    m = re.match(r"^([\d.]+)\s*H$", s, re.I)
    if m:
        return float(m.group(1)) * 60
    m = re.match(r"^(\d+):(\d+)$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return None


def is_implausible_pace(distance_km: float, duration: str, max_kmh: float = 100.0) -> bool:
    """거리/소요시간으로 계산한 속도가 도보·자전거 코스로 불가능한 수준이면 True."""
    mins = parse_minutes(duration)
    if not mins or mins <= 0 or distance_km <= 0:
        return False
    pace = distance_km / (mins / 60)
    return pace > max_kmh


def main():
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    records = raw["records"]
    print(f"원본 {len(records)}건 로드")

    trails = []
    seen_slugs = set()
    for i, r in enumerate(records):
        name = (r.get("길명") or "").strip()
        if not name:
            continue

        start_addr = (r.get("시작지점소재지지번주소") or "").strip()
        start_road = (r.get("시작지점도로명주소") or "").strip()
        end_addr = (r.get("종료지점소재지지번주소") or "").strip()
        end_road = (r.get("종료지점소재지도로명주소") or "").strip()

        do_nm, sigungu_nm = parse_sido_sigungu(start_addr or start_road)

        slug = slugify(name, i)
        if slug in seen_slugs:
            slug = f"{slug}-{i}"
        seen_slugs.add(slug)

        duration = (r.get("총소요시간") or "").strip()
        distance_km = parse_distance(r.get("총길이"))
        if is_implausible_pace(distance_km, duration):
            print(f"  [이상치 제외] {name}: {distance_km}km / {duration}")
            distance_km = 0.0

        trails.append({
            "id": i,
            "slug": slug,
            "name": name,
            "intro": (r.get("길소개") or "").strip(),
            "distanceKm": distance_km,
            "duration": duration,
            "startName": (r.get("시작지점명") or "").strip(),
            "startAddr": start_road or start_addr,
            "endName": (r.get("종료지점명") or "").strip(),
            "endAddr": end_road or end_addr,
            "routeInfo": (r.get("경로정보") or "").strip(),
            "manager": (r.get("관리기관명") or "").strip(),
            "managerTel": (r.get("관리기관전화번호") or "").strip(),
            "updatedDate": (r.get("데이터기준일자") or "").strip(),
            "provider": (r.get("제공기관명") or "").strip(),
            "doNm": do_nm,
            "sigunguNm": sigungu_nm,
        })

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(trails, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"변환 완료: {len(trails)}건 -> {OUT}")

    no_region = sum(1 for t in trails if not t["doNm"])
    print(f"지역 파싱 실패: {no_region}건")


if __name__ == "__main__":
    main()
