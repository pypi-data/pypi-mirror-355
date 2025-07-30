"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
import numpy as np
import pandas as pd

#Outlier Detection using Z-score (for normal distribution)

import numpy as np


def detect_outliers_zscore(data, columns, threshold=3):
    """
    Detects outliers using the Z-score method for the specified columns.
    :param data: DataFrame
    :param columns: List of columns to check for outliers
    :param threshold: Z-score value above which data will be considered as an outlier
    :return: DataFrame with outliers replaced by NaN
    """
    for column in columns:
        mean = np.mean(data[column])
        std_dev = np.std(data[column])
        z_scores = [(x - mean) / std_dev for x in data[column]]
        data[column] = [x if abs(z) <= threshold else np.nan for x, z in zip(data[column], z_scores)]

    return data

#Outlier Detection using IQR (for skewed distributions)

def detect_outliers_iqr(data, columns, lower_quantile=0.25, upper_quantile=0.75, factor=1.5):
    """
    Detects outliers using the IQR (Interquartile Range) method.
    :param data: DataFrame
    :param columns: List of columns to check for outliers
    :param lower_quantile: Lower quartile (default is 0.25)
    :param upper_quantile: Upper quartile (default is 0.75)
    :param factor: Multiplier for determining the outlier threshold (default is 1.5)
    :return: DataFrame with outliers replaced by NaN
    """
    for column in columns:
        Q1 = data[column].quantile(lower_quantile)
        Q3 = data[column].quantile(upper_quantile)
        IQR = Q3 - Q1
        lower_bound = Q1 - (IQR * factor)
        upper_bound = Q3 + (IQR * factor)
        data[column] = [x if lower_bound <= x <= upper_bound else np.nan for x in data[column]]

    return data

#Cap or Clip Outliers

def cap_outliers(data, columns, lower_percentile=0.05, upper_percentile=0.95):
    """
    Caps outliers in the specified columns by replacing them with the values from the specified percentiles.
    :param data: DataFrame
    :param columns: List of columns to apply capping
    :param lower_percentile: Lower percentile (default is 5th percentile)
    :param upper_percentile: Upper percentile (default is 95th percentile)
    :return: DataFrame with capped outliers
    """
    for column in columns:
        lower = data[column].quantile(lower_percentile)
        upper = data[column].quantile(upper_percentile)
        data[column] = data[column].clip(lower=lower, upper=upper)

    return data

#Replace Outliers with the Median
def replace_outliers_with_median(data, columns, threshold=3):
    """
    Replaces outliers with the median of each column.
    :param data: DataFrame
    :param columns: List of columns to check for outliers
    :param threshold: Z-score value above which data will be considered as an outlier
    :return: DataFrame with outliers replaced by the column median
    """
    for column in columns:
        mean = np.mean(data[column])
        std_dev = np.std(data[column])
        z_scores = [(x - mean) / std_dev for x in data[column]]
        median = np.median(data[column])
        data[column] = [median if abs(z) > threshold else x for x, z in zip(data[column], z_scores)]

    return data

