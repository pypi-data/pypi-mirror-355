# profiler.py

import pandas as pd
import numpy as np

def profile_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs a detailed exploratory data analysis on a pandas DataFrame.

    This function generates a comprehensive statistical summary for each column,
    differentiating between numerical and categorical data types to provide
    relevant metrics for each.

    Args:
        df (pd.DataFrame): The input DataFrame to analyze.

    Returns:
        pd.DataFrame: A DataFrame where each row corresponds to a column from the
                      input df and each column is a calculated statistic.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    print(f"DataFrame Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("-" * 30)

    stats_list = []
    for col in df.columns:
        # Basic Info
        non_missing_count = df[col].count()
        missing_count = df[col].isnull().sum()
        missing_percent = (missing_count / len(df)) * 100 if len(df) > 0 else 0

        # Initialize stats dictionary
        col_stats = {
            'column_name': col,
            'dtype': df[col].dtype,
            'non_missing_count': non_missing_count,
            'missing_count': missing_count,
            'missing_percent': f"{missing_percent:.2f}%"
        }

        # Differentiate between numerical and categorical/object columns
        if pd.api.types.is_numeric_dtype(df[col]):
            # Numerical statistics
            std_dev = df[col].std()
            mean_val = df[col].mean()
            cv = (std_dev / mean_val) * 100 if mean_val != 0 else np.nan

            p = df[col].quantile([0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
            iqr = p.get(0.75, np.nan) - p.get(0.25, np.nan)

            numerical_stats = {
                'min': df[col].min(),
                'percentile_1': p.get(0.01),
                'percentile_5': p.get(0.05),
                'percentile_10': p.get(0.10),
                'percentile_25': p.get(0.25),
                'percentile_50_median': p.get(0.50),
                'mean': mean_val,
                'percentile_75': p.get(0.75),
                'percentile_90': p.get(0.90),
                'percentile_95': p.get(0.95),
                'percentile_99': p.get(0.99),
                'max': df[col].max(),
                'iqr': iqr,
                'std_dev': std_dev,
                'coeff_of_variation': cv,
                'skewness': df[col].skew(),
                'kurtosis': df[col].kurt(),
                'num_zeros': (df[col] == 0).sum()
            }
            col_stats.update(numerical_stats)

        else:  # Categorical/Object
            # Using .dropna() to count unique values among non-missing data
            unique_vals = df[col].dropna().unique()
            col_stats['unique_count'] = len(unique_vals)

            if len(unique_vals) > 50:
                col_stats['unique_values_list'] = f"High Cardinality ({len(unique_vals)})"
            else:
                col_stats['unique_values_list'] = list(unique_vals)

            # Mode statistics for categorical columns
            if non_missing_count > 0:
                mode_series = df[col].mode()
                if not mode_series.empty:
                    mode_val = mode_series.iloc[0]
                    mode_freq = df[col].value_counts().get(mode_val, 0)
                    mode_percent = (mode_freq / non_missing_count) * 100 if non_missing_count > 0 else 0
                    categorical_stats = {
                        'mode': mode_val,
                        'mode_frequency': mode_freq,
                        'mode_percent': f"{mode_percent:.2f}%"
                    }
                    col_stats.update(categorical_stats)

        stats_list.append(col_stats)

    # Create the final summary DataFrame
    summary_df = pd.DataFrame(stats_list)
    summary_df.set_index('column_name', inplace=True)

    # Reorder columns for better readability
    column_order = [
        'dtype', 'non_missing_count', 'missing_count', 'missing_percent',
        # Categorical specific
        'unique_count', 'unique_values_list', 'mode', 'mode_frequency', 'mode_percent',
        # Numerical specific
        'mean', 'std_dev', 'coeff_of_variation', 'skewness', 'kurtosis', 'num_zeros',
        'min', 'percentile_1', 'percentile_5', 'percentile_10', 'percentile_25',
        'percentile_50_median', 'percentile_75', 'iqr', 'percentile_90', 'percentile_95',
        'percentile_99', 'max'
    ]
    
    # Use reindex to ensure all columns are present, filling with NaN if they don't apply
    # This also handles cases where a column might not exist for a given data type
    summary_df = summary_df.reindex(columns=column_order)

    return summary_df
