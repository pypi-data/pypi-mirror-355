"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""

def min_max_scale(data, column):
    values = [row[column] for row in data if isinstance(row[column], (int, float))]
    if not values:
        return data
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val
    if range_val == 0:

       for row in data:
           if isinstance(row[column], (int, float)):
              row[column] = (row[column] - min_val) / range_val
    return data

def min_max_scale_multiple(data, columns):
    for col in columns:
        data = min_max_scale(data, col)
    return data
