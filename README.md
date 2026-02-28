# reinfolib-skill

Claude Code スキル。住所を伝えるだけで、国土交通省の不動産取引データから坪単価・一種単価のレンジを自動分析する。

SKILL.md 1ファイルで全ロジックが完結。コードは1行も書いていない。

## セットアップ

### 1. API キーを取得する（無料）

[不動産情報ライブラリ API 利用申請](https://www.reinfolib.mlit.go.jp/help/apiManual/) からAPIキーを取得する。

### 2. MCP サーバーを入れる

このスキルは [mlit-geospatial-mcp](https://github.com/chirikuuka/mlit-geospatial-mcp)（国交省 API との橋渡し）が必要。

```bash
git clone https://github.com/chirikuuka/mlit-geospatial-mcp.git
cd mlit-geospatial-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Claude Code に MCP サーバーを登録する

`.mcp.json` をプロジェクトルートに作成するか、グローバル設定に追加する。

```json
{
  "mcpServers": {
    "mlit-geospatial-mcp": {
      "command": "/absolute/path/to/mlit-geospatial-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/mlit-geospatial-mcp/src/server.py"],
      "env": {
        "LIBRARY_API_KEY": "あなたのAPIキー"
      }
    }
  }
}
```

`/absolute/path/to/` は実際のパスに置き換える。

### 4. スキルをインストールする

```bash
npx skills add ramenumaiwhy/reinfolib-skill
```

## 使い方

Claude Code に話しかけるだけ。

```
赤坂1丁目の土地の相場教えて
```

## 出力内容

- 用途地域・建蔽率・容積率
- 地価公示（最寄り）
- 土地のみ取引の坪単価レンジ（用途地域別・最小/中央値/最大）
- 一種単価（容積率を考慮した比較指標）
- 建物込み取引からの推定土地坪単価（参考値）

## データソース

[国土交通省 不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/) API を使用。

> このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。
