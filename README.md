# reinfolib-plugin

Claude Code プラグイン。住所を入力するだけで、国土交通省の不動産取引データから坪単価・一種単価のレンジを自動分析する。

## 前提

- [mlit-geospatial-mcp](https://github.com/ramenumaiwhy/mlit-geospatial-mcp) が MCP サーバーとして稼働していること
- 不動産情報ライブラリの [API キー（無料）](https://www.reinfolib.mlit.go.jp/help/apiManual/) を取得済みであること

## インストール

```bash
claude plugin add /path/to/reinfolib-plugin
```

## 使い方

### スラッシュコマンド

```
/price-check 港区赤坂1丁目
```

### 自然言語

```
赤坂1丁目の土地の相場教えて
```

どちらでも同じ分析が実行される。

## 出力内容

- 用途地域・建蔽率・容積率
- 地価公示（最寄り）
- 土地のみ取引の坪単価レンジ（用途地域別・最小/中央値/最大）
- 一種単価（容積率を考慮した比較指標）
- 建物込み取引からの推定土地坪単価（参考値）

## ファイル構成

```
.claude-plugin/plugin.json   # プラグイン定義
commands/price-check.md       # /price-check コマンド
skills/price-analysis/SKILL.md # 分析手順書（Claude が参照する業務マニュアル）
```

## データソース

[国土交通省 不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/) API を使用。

> このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。
