"""CSV handling utilities."""
import csv


def save_to_csv(data, filename, fieldnames):
    """
    Save data to CSV file.

    Args:
        data: List of dictionaries
        filename: Output CSV filename
        fieldnames: List of field names
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def read_from_csv(filename):
    """
    Read data from CSV file.

    Args:
        filename: CSV filename to read

    Returns:
        list: List of dictionaries
    """
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
