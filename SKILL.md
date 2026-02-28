---
name: reinfolib-skill
description: 住所を入力するだけで、国土交通省の不動産取引データから坪単価・一種単価のレンジを自動分析する
---

# 不動産相場分析・価格妥当性検証スキル

## トリガー

以下のような不動産価格に関する質問・依頼:
- 「〇〇の相場教えて」「〇〇の土地いくらくらい？」「〇〇の坪単価」
- 「〇〇の地価」「〇〇の不動産価格」「〇〇のマンション相場」
- 「この物件高い？安い？」「売買価格は適正？」「価格の妥当性」
- 「〇〇の土地の値段」「一種単価」「不動産価格チェック」
- 「〇〇で家買いたいけど相場感知りたい」

## 前提条件（不動産鑑定実務基準に基づく）

- **時間的範囲**: 直近3年（運用上の便宜的範囲。市況変動が大きい局面では短縮を検討）
- **地理的範囲**: 同一需給圏内（同一 DistrictName。広域比較が必要な場合は隣接地域も参照）
- **有効件数**: 土地のみ取引3件以上で暫定参考値、20件以上で信頼度高
- **異常値除外**: 坪単価が地域中央値の1/5以下（特殊事情の可能性）。件数不足時は TradePrice ≤ 10万円をフォールバック基準とする

## MCPツールの準備

分析開始前に必ず ToolSearch で MCPツールを読み込む:
```
ToolSearch: "+mlit"
```

## 分析フロー

### 1. 住所 → 座標変換

国土地理院ジオコーダで座標を取得する:
```bash
python3 -c "
import json, sys, urllib.request, urllib.parse
q = '<住所>'
url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(q)
data = json.loads(urllib.request.urlopen(url).read())
if data:
    lon, lat = data[0]['geometry']['coordinates']
    print(f'lat={lat}, lon={lon}')
else:
    print('ERROR: 住所が見つかりません')
    sys.exit(1)
"
```

失敗時はエラー報告して終了。

### 2. 用途地域の確認

`mcp__mlit-geospatial-mcp__get_zoning_district` で用途地域・建蔽率・容積率を取得。
- タイムアウト時はスキップ可（後続の分析には必須ではない）
- 結果を変数として保持（容積率は一種単価の計算に必要）

### 3. 地価公示・地価調査データの取得

`mcp__mlit-geospatial-mcp__get_land_price_point_by_location` で地価公示・調査データを取得。
- 近隣の公示地価を参考値として記録

### 4. 取引データの取得（3年分）

`mcp__mlit-geospatial-mcp__get_multi_api` を以下のパラメータで3回呼び出し:
- `target_apis`: [1]
- `lat`: (Step 1の緯度)
- `lon`: (Step 1の経度)
- `save_file`: false
- `year`: 現在年, 前年, 前々年（例: 2025, 2024, 2023）

3年分のデータを結合する。

### 5. 土地のみ取引の分析

Type=「宅地(土地のみ)」のレコードをフィルタ:

```python
import statistics

# フィルタ: 土地のみ取引 & 異常値除外
land_only = [
    item for item in all_data
    if item.get("Type") == "宅地(土地のみ)"
    and item.get("TradePrice") and int(item["TradePrice"]) > 100000
]

for item in land_only:
    area_m2 = float(item.get("Area", 0))
    price = int(item["TradePrice"])
    if area_m2 > 0:
        tsubo_price = price / area_m2 * 3.30579  # 坪単価
        # 一種単価 = 坪単価 ÷ (容積率 / 100)
        # 容積率は item の FloorAreaRatio（指定容積率）を使用。前面道路制限による実効容積率は未考慮
        floor_area_ratio = float(item.get("FloorAreaRatio") or 0)
        ikishu_price = (tsubo_price / (floor_area_ratio / 100)) if floor_area_ratio > 0 else None
```

用途地域別にグルーピングしてレンジ（最小・中央値・最大）を算出。

### 6. 建物込み取引の分析（参考値）

Type=「宅地(土地と建物)」**のみ**をフィルタ。「中古マンション等」は**除外**する。

**中古マンション除外の理由**: マンションは土地持分（敷地権割合）構造が異なるため、TradePrice − 建物残価 = 土地価格とはならない。

#### 建物残価の簡易推定

法定耐用年数（住宅用途、減価償却資産の耐用年数等に関する省令 別表第一）:
- 木造(W): 22年
- 軽量鉄骨・肉厚3mm以下(LS-thin): 19年
- 軽量鉄骨・肉厚3mm超4mm以下(LS): 27年
- 重量鉄骨・肉厚4mm超(S): 34年
- RC/SRC: 47年

※ XIT001データのStructureフィールドでは肉厚を判別できないため、「軽量鉄骨造」は27年（保守的に長い方）を適用する。

標準建築費単価（2024年建築着工統計 第34表・住宅・全国計・1㎡あたり工事費予定額）:
- 木造: 21.5万円/㎡
- 鉄骨造(LS/S): 32.5万円/㎡
- RC: 33.4万円/㎡
- SRC: 33.5万円/㎡

Structure フィールドの判定（順序重要 — SRC/RCを鉄骨より先に判定すること）:
- 「ＳＲＣ（鉄骨鉄筋コンクリート造）」→ SRC
- 「ＲＣ（鉄筋コンクリート造）」→ RC
- 「軽量鉄骨造」→ LS
- 「鉄骨造」→ S
- 「木造」「ＷＳ（木造ストーンウォール）」→ 木造

計算式:
```python
import datetime

def estimate_land_price(item):
    """建物込み取引から土地価格を推定"""
    trade_price = int(item.get("TradePrice", 0))
    total_floor_area = item.get("TotalFloorArea")
    building_year = item.get("BuildingYear")
    structure = item.get("Structure", "")

    if not all([trade_price, total_floor_area, building_year]):
        return None

    # 面積のパース（"100" や "150" 等の文字列）
    try:
        floor_area = float(total_floor_area)
    except (ValueError, TypeError):
        return None

    # 築年数の計算（BuildingYear は "令和5年" "平成20年" 等の形式）
    current_year = datetime.date.today().year
    built_year = convert_japanese_year(building_year)  # 和暦→西暦変換
    if not built_year:
        return None
    age = current_year - built_year

    # 耐用年数・建築費単価の判定（SRC/RCを鉄骨より先に判定 — SRCに「鉄骨」が含まれるため）
    if "ＳＲＣ" in structure:
        useful_life, unit_cost = 47, 335000
    elif "ＲＣ" in structure:
        useful_life, unit_cost = 47, 334000
    elif "軽量鉄骨" in structure:
        useful_life, unit_cost = 27, 325000
    elif "鉄骨" in structure:
        useful_life, unit_cost = 34, 325000
    elif "木造" in structure or "ＷＳ" in structure:
        useful_life, unit_cost = 22, 215000
    else:
        useful_life, unit_cost = 22, 215000  # 不明時は木造として保守的に推定

    # 建物残価 = 建築費単価 × 延床面積 × max(0, 1 - 築年数/耐用年数)
    remaining_ratio = max(0, 1 - age / useful_life)
    building_value = unit_cost * floor_area * remaining_ratio

    # 推定土地価格
    estimated_land_price = trade_price - building_value
    if estimated_land_price <= 0:
        return None  # 異常値として除外

    return estimated_land_price


def convert_japanese_year(year_str):
    """和暦・西暦を西暦に変換"""
    import re
    if not year_str:
        return None
    # 元年対応: 「令和元年」→「令和1年」
    year_str = year_str.replace("元年", "1年")
    # 和暦パターン
    patterns = [
        (r"令和(\d+)年", lambda m: 2018 + int(m.group(1))),
        (r"平成(\d+)年", lambda m: 1988 + int(m.group(1))),
        (r"昭和(\d+)年", lambda m: 1925 + int(m.group(1))),
    ]
    for pattern, converter in patterns:
        m = re.search(pattern, year_str)
        if m:
            return converter(m)
    # 西暦表記（"2024年" 等）
    m = re.search(r"(\d{4})年", year_str)
    if m:
        return int(m.group(1))
    return None
```

#### ガード条件
- 推定土地価格が 0 以下 → 異常値として除外
- 建築費単価は全国平均であり地域差・仕様差が大きいため、建物込み推定の**判定重みは土地のみ取引より低く設定**

推定土地価格から坪単価を逆算し、土地のみ取引と比較検証する。

**注意**: この推定は簡易的なものであり、リフォーム・個別品質・設備は未考慮。**参考値**として提示し、判定の主軸にはしない。

### 7. 異常値除外

以下のレコードを除外:
- 坪単価が地域中央値の1/5以下（特殊事情の可能性）。中央値算出前の初回フィルタとして TradePrice ≤ 10万円をフォールバック適用
- 推定土地価格 ≤ 0（建物込みの場合）

### 8. 妥当性判定基準

※ 以下は運用上の便宜的閾値であり、不動産鑑定評価基準に定める公式基準ではない。実際の鑑定では事情補正・時点修正・地域要因・個別要因の比較が必要。

| 乖離率 | 判定 | 説明 |
|---------|------|------|
| ±10%以内 | 妥当 | 相場レンジ内 |
| 10-30% | 要精査 | 個別要因（接道、地形、嫌悪施設等）の可能性 |
| 30%超 | 異常値の可能性大 | 詳細調査が必要 |

建物込み取引の判定には、建物残価の推定精度に幅がある旨を必ず付記する。

### 9. 出力フォーマット

以下のテーブル形式でレポートを出力:

```
## 不動産相場分析レポート: <住所>

### 基本情報
| 項目 | 値 |
|------|-----|
| 用途地域 | ... |
| 建蔽率 | ...% |
| 容積率 | ...% |
| 地価公示（最寄り） | ...円/㎡ |

### 土地取引の坪単価・一種単価レンジ（土地のみ取引）
| 用途地域 | 件数 | 坪単価(万円) | 一種単価(万円) |
|----------|------|-------------|---------------|
| ... | N件 | XX〜YY（中央値ZZ） | XX〜YY（中央値ZZ） |

### 建物込み取引からの推定土地坪単価（参考）
| 用途地域 | 件数 | 推定坪単価(万円) | 備考 |
|----------|------|-----------------|------|
| ... | N件 | XX〜YY（中央値ZZ） | 簡易推定・参考値 |

### 地価公示との比較
...

### 総合判定
...（妥当性の判定結果と根拠）

---
> このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。
> 建物込み取引の推定土地価格は、法定耐用年数に基づく簡易推定であり、リフォーム・個別品質・設備は未考慮です。参考値としてご利用ください。
```

## 注意事項

- 件数が3件未満の場合は「データ不足のため暫定参考値」と明記
- API の rate limit に注意（連続呼び出し間に1秒の待機を入れる）
- 取引時期による価格変動は考慮しない（3年の範囲内であれば時点修正は小さいと仮定）。ただし急騰・急落局面では2年に短縮を検討すること
