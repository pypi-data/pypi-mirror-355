import unittest
from unittest.mock import patch, mock_open
import pandas as pd
from hkopenai.hk_housing_mcp_server.tool_private_storage import (
    fetch_private_storage_data,
    get_private_storage
)

class TestPrivateStorage(unittest.TestCase):
    CSV_DATA = '''"PRIVATE   STORAGE  -  COMPLETIONS,   STOCK   AND   VACANCY",,,,,,,,
Year,Completions,Completions - Remarks,Stock at year end,Stock at year end - Remarks,Vacancy at year end,Vacancy at year end - Remarks,Vacancy as a % of stock,Vacancy as a % of stock - Remarks
1985,108600,,1910100,,61800,,0.032,
1986,110100,,2003400,,51800,,0.026,
1987,32600,,1889300,,4200,,0.002,
1988,214000,,2087500,,53000,,0.025,
1989,61100,,2085800,,58300,,0.028,
1990,76000,,2116000,,22500,,0.011,
1991,538400,,2756200,,283600,,0.103,
1992,474400,,3223800,,395700,,0.123,
1993,102900,,3263100,,208600,,0.064'''

    def setUp(self):
        self.mock_requests = patch('requests.get').start()
        mock_response = mock_open(read_data=self.CSV_DATA.encode('utf-8-sig'))()
        mock_response.encoding = 'utf-8-sig'
        mock_response.text = self.CSV_DATA
        self.mock_requests.return_value = mock_response
        self.addCleanup(patch.stopall)

    def test_fetch_private_storage_data(self):
        df = fetch_private_storage_data()
        self.assertEqual(len(df), 9)  # 9 years of data
        self.assertEqual(df.iloc[0]['Year'], 1985)
        self.assertEqual(df.iloc[0]['Completions'], 108600)
        self.assertEqual(df.iloc[0]['Vacancy as a % of stock'], 0.032)

    def test_get_private_storage_default(self):
        result = get_private_storage()
        self.assertEqual(len(result), 9)
        self.assertEqual(result[0]['Year'], 1985)
        self.assertEqual(result[0]['Vacancy as a % of stock'], 0.032)

    def test_get_private_storage_year_filter(self):
        result = get_private_storage(year=1990)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Year'], 1990)
        self.assertEqual(result[0]['Vacancy as a % of stock'], 0.011)

if __name__ == "__main__":
    unittest.main()
