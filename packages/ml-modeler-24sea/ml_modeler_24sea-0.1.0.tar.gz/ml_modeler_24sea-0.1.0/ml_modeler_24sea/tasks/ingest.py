# -*- coding: utf-8 -*-
"""Ingest step for the data collection. The functions defined in this file serve
as a template for the data gathering step in a Prefect flow, and are expected
to be sufficient for most use cases, with little to no modification.
Using Prefect is not a necessary requirement, and it is done here as an example
of how to use an orchestrator to manage ML workflows.

The main function to be used for the data collection into a DataFrame is the
``ingest_flow``, which, if Prefect is used, should be decorated with the
`@flow` decorator. It works in combination with configuration files.
Specifically for the ingest step, the main configurations of interest are the
general.yaml and ingest.yaml files in which parameters such as the period to
gather data, and the specific metrics to retrieve can be specified.
"""
from __future__ import annotations

from asyncio import run as R
from datetime import datetime

import pandas as pd
from api_24sea.core import AsyncAPI
from prefect import task
from prefect.cache_policies import INPUTS, TASK_SOURCE

api = AsyncAPI()


@task(
    result_serializer="pickle",
    persist_result=True,
    cache_policy=INPUTS + TASK_SOURCE,
)
def load_data_api(
    site: str,
    training_turbines: list[str] | str,
    start_timestamp: str | datetime,
    end_timestamp: str | datetime,
    parameters: list[str],
) -> list[pd.DataFrame]:
    """
    Function to load data from the api

    Parameters
    ----------
    site : str
        The windfarm name
    training_turbines : list[str] | str
        Full names of the training turbines
    dt_start : str | datetime
        Starting date to load data
    dt_stop : str | datetime
        Ending date to load data
    parameters : list[str]
        A list of all parameters to load

    Returns
    -------
    list[pd.DataFrame]
        A list of each turbines dataframe
    """

    if isinstance(training_turbines, str):
        training_turbines = [training_turbines]
    data = R(
        api.get_data(
            [site],
            training_turbines,
            parameters,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
        )
    )
    dfs = list(data.datasignals.as_dict()[site.lower()].values())
    if not dfs:
        raise ValueError(
            "Empty list of dataframes loaded from the 24SEA API."
            " Please verify the selected parameters and period."
        )

    return dfs


@task
def combine_training_data_into_single_df(
    df_list: list[pd.DataFrame], add_location_column: bool = False
) -> pd.DataFrame:
    """
    Combine data from all turbines in a list of DataFrames into a single
    DataFrame.

    Parameters
    ----------
    df_list : list[pd.DataFrame]
        A list of dataframes containing the data from each turbine
    add_location_column : bool
        Whether to add a location column which contains the location ids of the
        original dataframes, by default False

    Returns
    -------
    pd.DataFrame
        Combined DataFrame with data from all turbines and loc_id and site_id
        removed from the column names.
    """
    for df in df_list:
        split_col_name = df.columns[0].split("_")
        site_id = split_col_name[1]
        loc_id = split_col_name[2]
        df.columns = df.columns.str.replace(f"{site_id}_{loc_id}_", "")
        if add_location_column:
            df.loc[:, "location"] = loc_id
    full_df = pd.concat(
        [df for df in df_list], axis=0  # pylint: disable=R1721
    ).reset_index(drop=True)
    return full_df.dropna(axis=1, how="all")
