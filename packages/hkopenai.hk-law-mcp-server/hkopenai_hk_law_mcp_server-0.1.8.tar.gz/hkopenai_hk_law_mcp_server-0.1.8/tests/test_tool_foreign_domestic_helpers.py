import unittest
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, List, Union, Any
from hkopenai.hk_law_mcp_server.foreign_domestic_helpers import (
    fetch_fdh_data,
    get_fdh_statistics
)

class TestForeignDomesticHelpers(unittest.TestCase):
    CSV_DATA = '''As at end of Year,Philippines,Indonesia,Others,Total
2016,189105,154073,8335,351513
2017,201090,159613,8948,369651
2018,210897,165907,9271,386075
2019,219073,170828,9419,399320
2020,207402,157802,8680,373884
2021,191783,140057,7611,339451
2022,190059,139961,8169,338189
2023,199516,147597,9118,356231
2024,202972,155577,9422,367971'''

    def setUp(self):
        self.mock_requests = patch('requests.get').start()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = self.CSV_DATA
        mock_response.encoding = 'utf-8'
        self.mock_requests.return_value = mock_response
        self.addCleanup(patch.stopall)

    def test_fetch_fdh_data(self):
        data: List[Dict[str, str]] = fetch_fdh_data()
        self.assertEqual(len(data), 9)
        self.assertEqual(data[0]['As at end of Year'], '2016')
        self.assertEqual(int(data[0]['Philippines']), 189105)
        self.assertEqual(int(data[0]['Total']), 351513)

    def test_get_fdh_statistics_default(self):
        result: Dict[str, Any] = get_fdh_statistics()
        self.assertIn('data', result)
        data = result['data']

        self.assertEqual(len(data), 9)
        self.assertEqual(data[0]['As at end of Year'], '2016')
        self.assertEqual(int(data[0]['Philippines']), 189105)
        self.assertEqual(int(data[0]['Total']), 351513)

    def test_get_fdh_statistics_year_filter(self):
        result: Dict[str, Any] = get_fdh_statistics(year=2020)
        self.assertIn('data', result)
        data = result['data']
        self.assertEqual(data['As at end of Year'], '2020')
        self.assertEqual(int(data['Philippines']), 207402)
        self.assertEqual(int(data['Total']), 373884)

    def test_get_fdh_statistics_year_not_found(self):
        result: Dict[str, Any] = get_fdh_statistics(year=2030)
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'No data for year 2030')

if __name__ == "__main__":
    unittest.main()
