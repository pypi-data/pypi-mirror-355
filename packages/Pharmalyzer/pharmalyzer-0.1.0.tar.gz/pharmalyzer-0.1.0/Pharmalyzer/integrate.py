"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""

def integrate_matrices_with_header(matrix1, headers1, matrix2, headers2, base_on='headers1'):
    """
    ترکیب دو ماتریس بر اساس ترتیب ستون‌های مشخص شده.

    پارامترها:
        matrix1, headers1: ماتریس و هدر اول
        matrix2, headers2: ماتریس و هدر دوم
        base_on (str): 'headers1' یا 'headers2' برای مشخص کردن مبنای ترتیب ستون

    خروجی:
        combined_matrix, final_headers
    """
    if base_on not in ['headers1', 'headers2']:
        raise ValueError("base_on must be 'headers1' or 'headers2'")

    final_headers = headers1 if base_on == 'headers1' else headers2

    def reorder_matrix(matrix, original_headers):
        index_map = {}
        for col in final_headers:
            if col in original_headers:
                index_map[col] = original_headers.index(col)
            else:
                raise ValueError(f"Column '{col}' not found in headers: {original_headers}")

        reordered = []
        for row in matrix:
            reordered.append([row[index_map[col]] if col in index_map else None for col in final_headers])
        return reordered

    matrix1_reordered = reorder_matrix(matrix1, headers1)
    matrix2_reordered = reorder_matrix(matrix2, headers2)

    combined_matrix = matrix1_reordered + matrix2_reordered

    return combined_matrix, final_headers


