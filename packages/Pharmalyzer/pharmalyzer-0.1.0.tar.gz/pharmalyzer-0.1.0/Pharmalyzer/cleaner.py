"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
def is_missing(val):
    return val in (None, '', 'None', 'null', 'NaN')

def try_parse(val):
    if is_missing(val):
        return None
    try:
        return float(val)
    except ValueError:
        return val

def fill_missing_with_mean(data, columns):
    for col in columns:
        total = 0
        count = 0
        for row in data:
            val = row.get(col)
            if not is_missing(val):
                total += val
                count += 1
        mean = total / count if count else 0
        for row in data:
            if is_missing(row.get(col)):
                row[col] = mean
    return data

def fill_missing_with_value(data, columns, default='Unknown'):
    for col in columns:
        for row in data:
            if is_missing(row.get(col)):
                row[col] = default
    return data

def drop_missing_rows(data, columns):
    """Remove rows where any of the specified columns have missing values."""
    return [row for row in data if all(not is_missing(row.get(col)) for col in columns)]


def fill_missing_forward(data, columns):
    for col in columns:
        last_valid = None
        for row in data:
            if not is_missing(row.get(col)):
                last_valid = row[col]
            elif last_valid is not None:
                row[col] = last_valid
    return data

def fill_missing_backward(data, columns):
    for col in columns:
        next_valid = None
        for row in reversed(data):
            if not is_missing(row.get(col)):
                next_valid = row[col]
            elif next_valid is not None:
                row[col] = next_valid
    return data


from collections import Counter


def fill_missing_with_mode(data, columns):
    """Fill missing values in the specified columns with the most frequent value."""
    for col in columns:
        # Get all non-missing values in the column
        non_missing_values = [row[col] for row in data if not is_missing(row.get(col))]

        # If there are non-missing values, find the mode (most frequent)
        if non_missing_values:
            # Find the most frequent value
            most_frequent_value = Counter(non_missing_values).most_common(1)[0][0]

            # Fill missing values with the most frequent value
            for row in data:
                if is_missing(row.get(col)):
                    row[col] = most_frequent_value
    return data


import math


def euclidean_distance(row1, row2, columns):
    """Calculate Euclidean distance between two rows based on selected columns."""
    distance = 0
    for col in columns:
        if not is_missing(row1.get(col)) and not is_missing(row2.get(col)):
            distance += (row1[col] - row2[col]) ** 2
    return math.sqrt(distance)


def knn_impute(data, columns, k=3):
    """Impute missing values using K-Nearest Neighbors."""
    for col in columns:
        # Find rows with missing values
        rows_with_missing = [row for row in data if is_missing(row.get(col))]

        # Find rows without missing values (for nearest neighbors)
        rows_without_missing = [row for row in data if not is_missing(row.get(col))]

        for row in rows_with_missing:
            # List to store distances and corresponding values of neighbors
            distances = []
            for neighbor in rows_without_missing:
                # Calculate distance between the row with missing value and the neighbor
                distance = euclidean_distance(row, neighbor, columns)
                distances.append((distance, neighbor))

            # Sort the neighbors by distance and get the k-nearest neighbors
            distances.sort(key=lambda x: x[0])
            nearest_neighbors = distances[:k]

            # Take the average (or most common) of the k-nearest neighbors' values for the missing value
            neighbor_values = [neighbor[1][col] for _, neighbor in nearest_neighbors if
                               not is_missing(neighbor[1].get(col))]
            if neighbor_values:
                row[col] = sum(neighbor_values) / len(neighbor_values)  # Use the mean of neighbors
    return data


def clean_mistyped_values(data, column, correction_dict):
    """
    Correct common misspellings or inconsistencies in a categorical column.

    Parameters:
    - data: List of dictionaries (rows).
    - column: The column name where data might have inconsistencies (e.g., 'sex').
    - correction_dict: A dictionary of mappings where keys are incorrect values and values are the correct value.
    """
    for row in data:
        if not is_missing(row.get(column)):
            value = row[column]
            # If the value is in the correction dictionary, update it
            if value in correction_dict:
                row[column] = correction_dict[value]
    return data


from fuzzywuzzy import process


def clean_with_fuzzy_matching(data, column, choices, threshold=80):
    """
    Fix values using fuzzy matching. Values below a certain threshold will not be corrected.

    Parameters:
    - data: List of dictionaries (rows).
    - column: The column name where inconsistencies are to be fixed.
    - choices: List of valid categories (e.g., ['male', 'female']).
    - threshold: Minimum match score for fuzzy matching to consider a correction.
    """
    for row in data:
        if not is_missing(row.get(column)):
            value = row[column]
            # Find the best match in 'choices' using fuzzy matching
            match, score = process.extractOne(value, choices)
            # If the score is above the threshold, correct the value
            if score >= threshold:
                row[column] = match
    return data


def drop_na(data):
    """
    Remove missing values from a list.

    Args:
        data (list): A list of values.

    Returns:
        list: Filtered list without missing values.
    """
    return [x for x in data if not is_missing(x)]