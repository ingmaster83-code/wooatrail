# -*- coding: utf-8 -*-
"""_rawdata/list_raw_mountain.json + detail_raw_mountain.json -> _rawdata/mountains.json
wooatrail 기존 trails.json 스키마(doNm=전체도명, sigunguNm) 그대로 따름."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST_SRC = ROOT / "_rawdata" / "list_raw_mountain.json"
DETAIL_SRC = ROOT / "_rawdata" / "detail_raw_mountain.json"
OUT = ROOT / "_rawdata" / "mountains.json"

SIDO_ALIAS = {
    "강원도": "강원특별자치도",
    "전라북도": "전북특별자치도",
}

GWANGJU_HINTS = ("동구", "서구", "남구", "북구", "광산구")


def parse_sido_sigungu(addr):
    if not addr:
        return "", ""
    parts = addr.strip().split()
    if not parts:
        return "", ""
    sido = parts[0]
    if sido == "전남광주통합특별시":
        sigungu = parts[1] if len(parts) > 1 else ""
        sido = "광주광역시" if any(h in sigungu for h in GWANGJU_HINTS) else "전라남도"
        return sido, sigungu
    sido = SIDO_ALIAS.get(sido, sido)
    sigungu = parts[1] if len(parts) > 1 else ""
    return sido, sigungu


def strip_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").strip()
    return text


def slugify(name, idx):
    s = re.sub(r"[^\w가-힣]+", "-", name).strip("-")
    return f"m{idx}-{s}"


def main():
    list_items = json.loads(LIST_SRC.read_text(encoding="utf-8"))
    details = json.loads(DETAIL_SRC.read_text(encoding="utf-8"))

    out = []
    skipped = 0

    for idx, it in enumerate(list_items):
        cid = it["contentid"]
        detail = details.get(cid, {})

        name = (it.get("title") or "").strip()
        addr = (detail.get("addr1") or it.get("addr1") or "").strip()
        if not name or not addr:
            skipped += 1
            continue

        do_nm, sigungu = parse_sido_sigungu(addr)
        if not do_nm:
            skipped += 1
            continue

        overview = strip_html(detail.get("overview", ""))
        image = detail.get("firstimage") or it.get("firstimage") or ""
        lat = detail.get("mapy") or it.get("mapy") or ""
        lng = detail.get("mapx") or it.get("mapx") or ""

        usetime = strip_html(detail.get("usetime") or "")
        parking = (detail.get("parking") or "").strip()
        infocenter = strip_html(detail.get("infocenter") or "") or (detail.get("tel") or "")
        restdate = strip_html(detail.get("restdate") or "")

        out.append({
            "name": name,
            "doNm": do_nm,
            "sigunguNm": sigungu,
            "address": addr,
            "phone": infocenter,
            "latitude": lat,
            "longitude": lng,
            "slug": slugify(name, idx),
            "overview": overview,
            "image": image,
            "usetime": usetime,
            "restdate": restdate,
            "parking": parking if parking not in ("", "-") else "",
        })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"총 {len(list_items)}건 중 {len(out)}개 저장, {skipped}개 스킵 -> {OUT}")

    region_count = {}
    for s in out:
        region_count[s["doNm"]] = region_count.get(s["doNm"], 0) + 1
    print("지역별:", region_count)


if __name__ == "__main__":
    main()
