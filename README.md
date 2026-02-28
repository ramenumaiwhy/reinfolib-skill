# reinfolib-skill

Claude Code スキル。住所を入力するだけで、国土交通省の不動産取引データから坪単価・一種単価のレンジを自動分析する。

コードは1行も書いていない。SKILL.md 1ファイルで全て動く。

## 前提

- [mlit-geospatial-mcp](https://github.com/ramenumaiwhy/mlit-geospatial-mcp) が MCP サーバーとして稼働していること
- 不動産情報ライブラリの [API キー（無料）](https://www.reinfolib.mlit.go.jp/help/apiManual/) を取得済みであること

## インストール

SKILL.md を Claude Code のスキルディレクトリにコピーする。

```bash
mkdir -p ~/.claude/skills/reinfolib
cp SKILL.md ~/.claude/skills/reinfolib/SKILL.md
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
