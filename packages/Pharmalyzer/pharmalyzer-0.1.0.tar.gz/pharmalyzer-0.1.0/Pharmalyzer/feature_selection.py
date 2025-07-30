"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""

import csv
import math

def rank_features_by_variance(matrix, headers, descending=True, show_top=True, top_k=None, save_path=None, return_indices=False):
    """
    Compute and rank features by variance with extended options.

    Parameters:
        matrix (List[List[float]]): 2D dataset (rows of samples).
        headers (List[str]): Column names.
        descending (bool): Sort from high to low if True.
        show_top (bool): Print most/least variant features if True.
        top_k (int or None): Number of top features to return. If None, return all.
        save_path (str or None): If specified, save results to this CSV file.
        return_indices (bool): If True, return feature indices instead of names.

    Returns:
        List[Tuple[str or int, float]]: Sorted list of (feature, variance).
    """

    def compute_variance(values):
        n = len(values)
        if n == 0:
            return 0.0
        mean = sum(values) / n
        return sum((x - mean) ** 2 for x in values) / n

    if not matrix or not headers:
        return []

    num_cols = len(headers)
    columns = [[] for _ in range(num_cols)]

    for row in matrix:
        for i in range(min(len(row), num_cols)):
            try:
                val = float(row[i])
                if not math.isnan(val):
                   columns[i].append(float(row[i]))
            except (ValueError, TypeError):
                continue

    variances = {
        i if return_indices else headers[i]: compute_variance(columns[i])
        for i in range(num_cols)
        if columns[i]
    }

    sorted_features = sorted(variances.items(), key=lambda x: x[1], reverse=descending)

    if show_top and sorted_features:
        print(f"🔺 Highest variance: {sorted_features[0][0]} = {sorted_features[0][1]:.4f}")
        print(f"🔻 Lowest variance: {sorted_features[-1][0]} = {sorted_features[-1][1]:.4f}")

    if top_k is not None:
        sorted_features = sorted_features[:top_k]

    if save_path:
        with open(save_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Feature', 'Variance'])
            writer.writerows(sorted_features)

    return sorted_features
