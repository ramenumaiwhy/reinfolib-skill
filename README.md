# 土地の相場を調べる Claude Code スキル

「東京都港区赤坂一丁目の土地の相場は？」と質問すると、国土交通省「不動産情報ライブラリ」から同じ地区の取引事例を集め、用途地域ごとに坪単価と一種単価の件数・最小値・中央値・最大値を返します。土地のみの取引を主に使い、土地と建物の一括取引から求めた推定値は参考欄に載せます。

## セットアップ

Claude Code、Python 3.10以上、[不動産情報ライブラリのAPIキー](https://www.reinfolib.mlit.go.jp/api/request/)を用意します。以下はmacOS・Linuxの例です。

1. Claude Codeを使うプロジェクトにスキルを配置します。

   ```bash
   git clone https://github.com/ramenumaiwhy/reinfolib-skill.git .claude/skills/reinfolib-skill
   ```

2. 同じディレクトリから [mlit-geospatial-mcp](https://github.com/chirikuuka/mlit-geospatial-mcp) をセットアップします。固定版は通信時の証明書検証を無効にしているため、同梱の差分で証明書検証を有効にし、キー付き通信のリダイレクトを止めます。差分は取引0件と取得失敗を別の応答として返し、政令指定都市の区名表記にも対応します。サーバーが使うMCP SDKは1系です。

   ```bash
   git clone https://github.com/chirikuuka/mlit-geospatial-mcp.git
   (
     cd mlit-geospatial-mcp || exit 1
     git checkout dca3fd3 &&
       git apply ../.claude/skills/reinfolib-skill/patches/verify-tls.patch &&
       python3 -m venv .venv &&
       .venv/bin/python -m pip install -r requirements.txt 'mcp>=1,<2'
   )
   ```

3. プロジェクトの `.mcp.json` にサーバーを登録します。2か所のパスは手順2の配置先に置き換えます。キーはClaude Codeを起動する環境の `LIBRARY_API_KEY` に設定します。

   ```json
   {
     "mcpServers": {
       "mlit-geospatial-mcp": {
         "command": "/absolute/path/to/mlit-geospatial-mcp/.venv/bin/python",
         "args": ["/absolute/path/to/mlit-geospatial-mcp/src/server.py"],
         "env": { "LIBRARY_API_KEY": "${LIBRARY_API_KEY}" }
       }
     }
   }
   ```

4. プロジェクトでClaude Codeを起動し、`/mcp` で接続を確認します。住所は市区町村と町名までで調べられます。住所検索には国土地理院、取引の取得には上記のMCPサーバーを使います。

## 結果の読み方

一種単価は土地の坪単価を指定容積率の倍率で割った値です。容積率200%なら坪単価の半分になります。レポートには取得できた年と集計件数を載せます。建物残価は構造・築年・延床面積からの簡易推定です。

## 同じ取引データを使う作品

ColabやWebで土地を分析する入口は [reinfolib-service](https://github.com/ramenumaiwhy/reinfolib-service)、中古マンションの売出㎡単価を周辺取引と比較する入口は、そのフォークの [mansion-checker](https://github.com/ramenumaiwhy/mansion-checker) です。
