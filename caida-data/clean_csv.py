"""
This file opens the asn_rov_scores.csv file,
loads the csv (skips first row) and cleans the ASN column:
remove any char prefix (e.g., "AS", "s") and convert to int.
"""

import os
import csv
import re

if __name__ == '__main__':
    rovista_scores = {}
    with open(os.path.join(os.path.dirname(__file__), '../caida-data', 'asn_rov_scores.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asn = row.get('ASN')
            score = row.get('rovista_score')
            if asn is None or score is None:
                continue
            # Remove any "AS" prefix and convert to int
            asn = re.sub(r'^(?:as|s)', '', asn.strip(), flags=re.IGNORECASE)
            if not asn.isdigit():
                continue
            rovista_scores[int(asn)] = float(score)

    # Store it back to a new CSV file
    with open(os.path.join(os.path.dirname(__file__), '../caida-data', 'asn_rov_scores_cleaned.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ASN', 'rovista_score'])
        writer.writeheader()
        for asn, score in rovista_scores.items():
            writer.writerow({'ASN': asn, 'rovista_score': score})

    print(f"Loaded {len(rovista_scores)} ROV scores")