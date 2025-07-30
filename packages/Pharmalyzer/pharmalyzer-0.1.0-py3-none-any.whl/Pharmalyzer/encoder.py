"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
def label_encode(data, column):
    unique_vals = list({row[column] for row in data if row.get(column) is not None})
    mapping = {val: idx for idx, val in enumerate(sorted(unique_vals))}
    for row in data:
        if row.get(column) in mapping:
            row[column] = mapping[row[column]]
        else:
            row[column] = -1
    return data, mapping
