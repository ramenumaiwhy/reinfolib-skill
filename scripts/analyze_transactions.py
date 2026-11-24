"""XIT001 の取引属性リストを標準入力から受け、用途地域別の単価を万円/坪で返す。"""

import datetime
import json
import math
import re
import statistics
import sys
import unicodedata
from collections import defaultdict

# 住宅の構造別の耐用年数と2024年の全国建築費単価（円/㎡）
STRUCTURE_PARAMS = {
    "SRC": (47, 335000), "RC": (47, 334000), "軽量鉄骨": (27, 325000),
    "鉄骨": (34, 325000), "木造": (22, 215000),
}


def positive_number(value):
    try:
        number = float(value)
    except (ValueError, TypeError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def building_year(value):
    match = re.fullmatch(r"(?:(令和|平成|昭和))?(元|\d+)年?", value or "")
    if not match:
        return None
    era, year = match.groups()
    if not era and (year == "元" or len(year) != 4):
        return None
    offset = {"令和": 2018, "平成": 1988, "昭和": 1925, None: 0}[era]
    return offset + (1 if year == "元" else int(year))


def building_value(item, year):
    floor = positive_number(item.get("TotalFloorArea"))
    built = building_year(item.get("BuildingYear"))
    if floor is None or built is None or built > year:
        return None
    structure = unicodedata.normalize("NFKC", item.get("Structure") or "")
    key = next((k for k in STRUCTURE_PARAMS if k in structure), "木造")
    life, unit_cost = STRUCTURE_PARAMS[key]
    return floor * unit_cost * max(0, 1 - (year - built) / life)


def distribution(values):
    if not values:
        return {"count": 0}
    return {
        "count": len(values), "min": round(min(values), 1),
        "median": round(statistics.median(values), 1), "max": round(max(values), 1),
    }


def summarize(rows):
    threshold = statistics.median(row[1] for row in rows) / 5 if len(rows) >= 3 else 0
    zones = defaultdict(list)
    for zone, tsubo, ikishu in rows:
        if tsubo >= threshold:
            zones[zone].append((tsubo, ikishu))
    return {
        zone: {
            "tsubo": distribution([tsubo for tsubo, _ in prices]),
            "ikishu": distribution([ikishu for _, ikishu in prices if ikishu is not None]),
        }
        for zone, prices in zones.items()
    }


def analyze(items, year):
    land, with_building = [], []
    for item in items:
        price = positive_number(item.get("TradePrice"))
        area = positive_number(item.get("Area"))
        if price is None or area is None:
            continue
        if item.get("Type") == "宅地(土地のみ)":
            if price <= 100000:
                continue
            group = land
        elif item.get("Type") == "宅地(土地と建物)":
            residual = building_value(item, year)
            if residual is None or price <= residual:
                continue
            price -= residual
            group = with_building
        else:
            continue
        tsubo = price / area * 3.30579 / 10000
        far = positive_number(item.get("FloorAreaRatio"))
        zone = item.get("UseDistrict") or item.get("CityPlanning") or "不明"
        group.append((zone, tsubo, tsubo / (far / 100) if far else None))
    return {"land_only": summarize(land), "land_with_building": summarize(with_building)}


if __name__ == "__main__":
    items = json.load(sys.stdin)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        sys.exit("XIT001 の取引属性を JSON 配列で入力してください。")
    print(json.dumps(analyze(items, datetime.date.today().year), ensure_ascii=False, indent=2))
