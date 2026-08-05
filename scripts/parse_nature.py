# -*- coding: utf-8 -*-
"""_rawdata/list_raw_{river,waterfall,lake,cave,spring}.json + detail_raw_*.json -> _rawdata/nature_spots.json
wooatrail 기존 mountains.json 스키마(doNm=전체도명, sigunguNm) 그대로 따름."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_rawdata" / "nature_spots.json"

CATEGORIES = {
    "river": {"label": "강", "icon": "🏞️"},
    "waterfall": {"label": "폭포", "icon": "💦"},
    "lake": {"label": "호수", "icon": "🌊"},
    "cave": {"label": "동굴", "icon": "🕳️"},
    "spring": {"label": "약수터", "icon": "💧"},
}

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


def slugify(kind, name, idx):
    s = re.sub(r"[^\w가-힣]+", "-", name).strip("-")
    return f"n-{kind}-{idx}-{s}"


def parse_category(key, meta):
    list_src = ROOT / "_rawdata" / f"list_raw_{key}.json"
    detail_src = ROOT / "_rawdata" / f"detail_raw_{key}.json"
    list_items = json.loads(list_src.read_text(encoding="utf-8"))
    details = json.loads(detail_src.read_text(encoding="utf-8"))

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
            "slug": slugify(key, name, idx),
            "overview": overview,
            "image": image,
            "usetime": usetime,
            "restdate": restdate,
            "parking": parking if parking not in ("", "-") else "",
            "kind": key,
            "kindLabel": meta["label"],
            "kindIcon": meta["icon"],
        })

    print(f"[{key}] {len(list_items)}건 중 {len(out)}개 저장, {skipped}개 스킵")
    return out


def main():
    all_spots = []
    for key, meta in CATEGORIES.items():
        all_spots.extend(parse_category(key, meta))

    OUT.write_text(json.dumps(all_spots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n총 {len(all_spots)}개 -> {OUT}")

    region_count = {}
    for s in all_spots:
        region_count[s["doNm"]] = region_count.get(s["doNm"], 0) + 1
    print("지역별:", region_count)

    kind_count = {}
    for s in all_spots:
        kind_count[s["kindLabel"]] = kind_count.get(s["kindLabel"], 0) + 1
    print("유형별:", kind_count)


if __name__ == "__main__":
    main()
