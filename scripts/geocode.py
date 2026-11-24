#!/usr/bin/env python3
"""
住所 → 緯度経度変換スクリプト（国土地理院ジオコーダ使用）

使用方法:
  python3 scripts/geocode.py '東京都千代田区丸の内1丁目'

出力:
  lat=35.681236, lon=139.767125

"""

import json
import sys
import urllib.request
import urllib.parse


def geocode(address: str) -> tuple[float, float]:
    """住所を緯度・経度に変換する。"""
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(address)
    with urllib.request.urlopen(url, timeout=10) as res:
        data = json.loads(res.read())

    if not data:
        raise ValueError(f"住所が見つかりません: {address}")

    lon, lat = data[0]["geometry"]["coordinates"]
    return lat, lon


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 geocode.py '<住所>'", file=sys.stderr)
        sys.exit(1)

    address = sys.argv[1]
    try:
        lat, lon = geocode(address)
        print(f"lat={lat}, lon={lon}")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 座標取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
