"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
import pandas as pd

def remove_non_numerical_columns(data):
    """
    Removes non-numeric columns from the dataset.
    """
    return data.select_dtypes(include=['number'])

def drop_missing_threshold(data, col_thresh=0.5, row_thresh=0.5):
    """
    Drops columns and rows with missing data above a threshold.
    - col_thresh: minimum fraction of non-null values a column must have.
    - row_thresh: minimum fraction of non-null values a row must have.
    """
    data = data.dropna(axis=1, thresh=int(col_thresh * len(data)))
    data = data.dropna(axis=0, thresh=int(row_thresh * len(data.columns)))
    return data

def drop_discrete_columns(data, max_unique=5):
    """
    Drops categorical columns with low cardinality (discrete columns).
    """
    to_drop = [col for col in data.columns
               if data[col].dtype == 'object' and data[col].nunique() <= max_unique]
    return data.drop(columns=to_drop)

def drop_constant_columns(data):
    """
    Drops columns with the same value in all rows (zero variance).
    """
    return data.loc[:, data.nunique() > 1]

def drop_index_columns(data):
    """
    Drops columns that are likely to be index or case number identifiers.
    """
    likely_ids = [col for col in data.columns
                  if 'id' in col.lower() or 'case' in col.lower()]
    return data.drop(columns=likely_ids)

def clean_dataset(data, col_thresh=0.5, row_thresh=0.5, drop_discrete=True):
    """
    Runs a full cleaning pipeline:
    - Removes columns/rows with high missingness
    - Removes constant columns
    - Removes ID/case-like columns
    - Removes non-numeric columns
    - Optionally drops low-cardinality discrete columns
    """
    data = drop_missing_threshold(data, col_thresh, row_thresh)
    data = drop_constant_columns(data)
    data = drop_index_columns(data)
    data = remove_non_numerical_columns(data)
    if drop_discrete:
        data = drop_discrete_columns(data)
    return data



