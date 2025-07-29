from src.openpyutils.csv import csv_to_json


def test_csv_to_json():
    csv_to_json('data/test_data.csv', 'data/test_data.json')


test_csv_to_json()
