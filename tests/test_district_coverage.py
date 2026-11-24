"""同梱パッチを適用したMCPのsrcをPYTHONPATHに指定し、MCPのPythonで実行する。"""

import unittest
from unittest.mock import patch

from request_processor.service.apis import real_estate_api1


class DistrictCoverageTest(unittest.TestCase):
    def test_district_coverage(self):
        api = real_estate_api1.RealEstateApi1({}, {"muni_cd": "14104", "lv_01_nm": "本町一丁目"})
        matched = {"MunicipalityCode": "14104", "DistrictName": "本町"}
        elsewhere = {**matched, "DistrictName": "別地区"}
        unknown = {"TradePrice": "50000000"}

        cases = [
            ("空配列", [], []),
            ("地区外のみ", [elsewhere], []),
            ("所在地なし", [unknown], None),
            ("地区名なし", [{"MunicipalityCode": "14104"}], None),
            ("地区外と判定不能", [elsewhere, unknown], None),
            ("地区内と判定不能", [matched, unknown], [matched]),
        ]
        with (
            patch.object(real_estate_api1, "get_cityname", return_value="中区"),
            patch.object(real_estate_api1, "get_latlon", return_value=[139.64, 35.44]),
        ):
            for label, rows, expected in cases:
                with self.subTest(label), patch.object(api, "_call_api", return_value={"data": rows}):
                    result = api.exchange()
                    if expected is None:
                        self.assertIsNone(result)
                    else:
                        self.assertEqual(result["data"]["type"], "FeatureCollection")
                        self.assertEqual([f["properties"] for f in result["data"]["features"]], expected)
