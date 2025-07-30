# -*- coding: utf-8 -*-
"""
This module defines how to split the data into training and test sets.
"""

from __future__ import annotations

import pandas as pd
from prefect import task
from sklearn.model_selection import train_test_split as sklearn_train_test_split


@task
def train_test_split(
    df: pd.DataFrame, test_size: float = 0.8, random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Defines how the data is split into a train and test set."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame.")
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")

    train_df, test_df = sklearn_train_test_split(
        df, test_size=test_size, random_state=random_state
    )
    return train_df, test_df
