---
name: reinfolib-skill
description: Estimate Japanese land prices from comparable MLIT transactions when asked for 土地の相場, 坪単価, 一種単価, or to compare a land asking price with local sales.
---

## Find comparable transactions

Geocode the supplied Japanese municipality and district with `python3 "${CLAUDE_SKILL_DIR}/scripts/geocode.py" '<address>'`, passing the address as one literal argument. Confirm the location if the municipality is ambiguous. If the address cannot be resolved, ask for a more specific location.

Use `get_multi_api` on the connected mlit-geospatial-mcp server with the resulting lat/lon and `save_file: false` for every call. Request `target_apis: [3, 5]` together for nearby official land-price points and zoning. Mark missing context as unavailable.

Call `get_multi_api` with `target_apis: [1]` separately for the current year and the previous two years, spacing the requests. Read the JSON text of each successful response. For XIT001, collect the `properties` of each GeoJSON feature in `data.api_results[].data.features`. Keep the returned district and years with the data. Only a returned FeatureCollection with an empty features array confirms zero district transactions for that year. An error, a null API result (even under outer status "success"), or a malformed response means the year is unavailable. List these years separately from confirmed empty years and the years contributing comparable sales. If there are no comparable sales, report the coverage and stop.

## Calculate and report

Pass the combined list of transaction properties as a JSON array on standard input to `python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_transactions.py"`. Use its separate summaries for land-only sales and estimated land values from land-and-building sales. Read [the methodology](references/methodology.md) when explaining the filters or residual-value assumptions.

Report in Japanese. Give the district, covered years and, for each land-use zone, the sample count, minimum, median and maximum for each available metric in 万円/坪. Explain differences in sample counts when FAR is missing. Label building-derived figures as estimates. Give the date, unit and location of any official price point used for context. When the user supplies a comparable asking price and area, show its unit price and percentage difference from the relevant observed median. Flag small samples and avoid a verdict when comparable data is missing. State the limits of the estimate and include the source notice below.

> このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性、正確性、完全性等が保証されたものではありません。
