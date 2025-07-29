import csv
import json

from src.openpyutils import logger


# Function to convert CSV to JSON
def csv_to_json(csv_file_path, json_file_path):
    # Read the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
        # Convert CSV to a list of dictionaries
        csv_reader = csv.DictReader(csv_file)
        data = [row for row in csv_reader]

    # Write the data to a JSON file
    with open(json_file_path, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

    logger.info(f"CSV data has been successfully converted to JSON and saved to {json_file_path}")
    logger.suc(f"CSV data has been successfully converted to JSON and saved to {json_file_path}")
    logger.err(f"CSV data has been successfully converted to JSON and saved to {json_file_path}")
    logger.warn(f"CSV data has been successfully converted to JSON and saved to {json_file_path}")
    logger.fatal(f"CSV data has been successfully converted to JSON and saved to {json_file_path}")
