import zipfile, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "mountain"
OUT_GEO = ROOT / "_extracted2" / "geojson"
OUT_GPX = ROOT / "_extracted2" / "gpx"
OUT_GEO.mkdir(parents=True, exist_ok=True)
OUT_GPX.mkdir(parents=True, exist_ok=True)

def extract_one(zip_path: Path, out_dir: Path, ext: str):
    trail_id = zip_path.stem.split('_')[0]
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            # pick the file with matching extension (ignore mangled encoding, just check suffix)
            target = None
            for n in names:
                if n.lower().endswith(ext):
                    target = n
                    break
            if target is None and names:
                target = names[0]
            if target is None:
                return False
            data = z.read(target)
            (out_dir / f"{trail_id}.{ext}").write_bytes(data)
            return True
    except Exception as e:
        print(f"ERR {zip_path.name}: {e}")
        return False

geo_zips = sorted(SRC.glob("*_geojson.zip"))
gpx_zips = sorted(SRC.glob("*_gpx.zip"))

ok = 0
for i, z in enumerate(geo_zips):
    if extract_one(z, OUT_GEO, "json"):
        ok += 1
    if (i+1) % 500 == 0:
        print(f"geojson {i+1}/{len(geo_zips)}")
print(f"geojson 완료: {ok}/{len(geo_zips)}")

ok = 0
for i, z in enumerate(gpx_zips):
    if extract_one(z, OUT_GPX, "gpx"):
        ok += 1
    if (i+1) % 500 == 0:
        print(f"gpx {i+1}/{len(gpx_zips)}")
print(f"gpx 완료: {ok}/{len(gpx_zips)}")
