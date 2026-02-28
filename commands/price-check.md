---
name: price-check
description: "不動産の相場・坪単価・価格妥当性を分析。Triggers on: '〇〇の相場教えて', '〇〇の土地いくら', '〇〇の坪単価', '不動産価格チェック', '土地の値段', '一種単価', 'この物件高い？安い？', '売買価格は適正？', '〇〇の地価', 'マンション相場', '〇〇の不動産価格', 'price check'."
argument-hint: <住所>
---

# 不動産価格チェック

住所「$ARGUMENTS」の不動産相場分析を実行する。

## 実行手順（この順序を厳守すること）

### Step 0: MCPツール読み込み
ToolSearch で `+mlit` を検索し、MCPツールを利用可能にする。

### Step 1: 住所 → 座標変換
国土地理院ジオコーダで座標を取得:
```bash
python3 -c "
import json, sys, urllib.request, urllib.parse
q = '$ARGUMENTS'
url = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(q)
data = json.loads(urllib.request.urlopen(url).read())
if data:
    lon, lat = data[0]['geometry']['coordinates']
    print(f'{lat},{lon}')
else:
    print('ERROR')
    sys.exit(1)
"
```
失敗時はエラー報告して終了。

### Step 2: 用途地域の確認
`mcp__mlit-geospatial-mcp__get_zoning_district` を呼び出し:
- lat, lon: Step 1 の座標
- タイムアウト時はスキップ可

### Step 3: 地価公示データの取得
`mcp__mlit-geospatial-mcp__get_land_price_point_by_location` を呼び出し:
- lat, lon: Step 1 の座標

### Step 4: 取引データの取得（3年分）
以下を3回実行（year = 現在年, 前年, 前々年）。各呼び出し間に1秒待機:
`mcp__mlit-geospatial-mcp__get_multi_api`:
- target_apis: [1]
- lat, lon: Step 1 の座標
- year: 各年
- save_file: false

3年分のデータを結合する。

### Step 5: データ分析（Python）
Bash で python3 を実行し、以下を一括処理:

1. **土地のみ取引のフィルタと分析**:
   - Type=「宅地(土地のみ)」でフィルタ
   - 初回フィルタ: TradePrice ≤ 10万円除外 → 坪単価算出後、中央値の1/5以下も除外
   - 坪単価 = TradePrice ÷ Area(㎡) × 3.30579
   - 一種単価 = 坪単価 ÷ (指定容積率 / 100)
   - 用途地域別にグルーピング → 最小・中央値・最大を算出

2. **建物込み取引のフィルタと分析**（参考値）:
   - Type=「宅地(土地と建物)」でフィルタ（「中古マンション等」は除外）
   - Structure判定はSRC/RCを鉄骨より先に判定（SKILL.md参照）
   - BuildingYear・Structure・TotalFloorArea を使い建物残価を簡易推定
   - 推定土地価格 = TradePrice − 建物残価
   - 推定土地価格 ≤ 0 のレコードを除外
   - 推定土地坪単価を算出 → 用途地域別にグルーピング

3. **異常値除外のまとめ**:
   - 除外件数を記録（透明性のため）

### Step 6: レポート出力
skills/price-analysis/SKILL.md の「出力フォーマット」に従ってテーブル形式でレポートを出力。

必ず以下のクレジットを末尾に記載:
> このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。
> 建物込み取引の推定土地価格は、法定耐用年数に基づく簡易推定であり、リフォーム・個別品質・設備は未考慮です。参考値としてご利用ください。
