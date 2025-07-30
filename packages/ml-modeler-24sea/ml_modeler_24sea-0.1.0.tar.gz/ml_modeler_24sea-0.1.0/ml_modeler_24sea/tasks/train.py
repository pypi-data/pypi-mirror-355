# -*- coding: utf-8 -*-
"""Train step for the model training and logging into an MlFlow run. The
functions defined in this file serve as a template for the train step in a
Prefect flow. Using Prefect is not a necessary requirement, and it is done here
as an example of how to use an orchestrator to manage ML workflows.

The main function to be used for the training and logging of runs is the
``train_flow``, which, if Prefect is used, should be decorated with the
`@flow` decorator. It works in combination with configuration files.
Specifically for the train step, the main configurations of interest are the
general.yaml and train.yaml files in which parameters such as the
hyperparameters of the ML model (e.g learning rate) or general information to be
saved in MlFlow (start_validity_date of the model) can be specified.

.. warning::
    In order for the saved models to be able to function correctly within the
    AI API it is important that some functions defined here (e.g.
    create_signature, setup_mlflow_info etc) are not changed, and are always
    utilised in the indicated way. If a function must not be modified it will
    be clearly noted.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Union

import mlflow
import pandas as pd
import yaml
from mlflow.models.signature import ModelSignature
from mlflow.types import DataType
from mlflow.types.schema import ColSpec, Schema
from prefect import task

from ..misc.utils import parse_datetime_to_string


@task
def create_signature(
    input_columns: list[str], output_name: str
) -> ModelSignature:
    """
    .. warning::
        DO NOT CHANGE THIS FUNCTION UNLESS ABSOLUTELY NECESSARY. IT IS USED TO
        ENFORCE A STANDARD WAY OF CREATING THE MODEL SIGNATURES FOR THE MODELS.

    Create a model signature for the given input output columns. Will also add a
    timestamp input and output column to the schema.

    The signature is used to create the model schema in the AI API, meaning that
    if the created signature is missing required columns, predictions will not,
    be possible, while if it has redundant columns, more than the required
    inputs will be requested which will make the predictions more time  and
    resource demanding.

    Parameters
    ----------
    input_columns : list[str]
        The columns of the input dataframe before any preprocessing. So any
        models that are added in a preprocessing step should not be included.
        These types of columns must be calculated during inference within the
        .predict function of the model
    output_name : str
        The output column name.

    Returns
    -------
    ModelSignature
        The model signature to be used to validate the input and output data
    """

    # Create input schema
    input_cols = [
        ColSpec(DataType.double, col)
        for col in input_columns
        if col
        not in ["timestamp", "location", output_name.replace("_pred", "")]
    ]
    input_cols.append(ColSpec(DataType.string, "timestamp"))

    input_schema = Schema(input_cols)  # type: ignore
    # Ensure that output name ends with "_pred"
    if not output_name.endswith("_pred"):
        output_name += "_pred"

    # Create output schema
    output_schema = Schema(
        [
            ColSpec(DataType.double, output_name),
            ColSpec(DataType.string, "timestamp"),
        ]
    )
    # Create and return signature
    return ModelSignature(inputs=input_schema, outputs=output_schema)


@task
def create_input_example(input_columns: list[str]) -> pd.DataFrame:
    """
    Create an input example for the model based on the input columns.

    Assumes that all inputs are floating point values and assignes them the
    value of 1.0. Can be changed to something more realistic, like randomly
    assigning numbers toe ach input.

    Parameters
    ----------
    signature : list[str]
        the input columns exactly as they are in the signature.
    Returns
    -------
    pd.DataFrame
        The input example DataFrame
    """
    input_example = []
    single_input = {k: 1.0 for k in input_columns if len(k.split("_")) > 1}
    single_input["timestamp"] = "2022-11-01T00:00:00Z"  # type: ignore
    input_example.append(single_input)
    return pd.DataFrame(input_example)


@task
def setup_mlflow_info(
    site: str,
    locations: str | list[str],
    output_name: str,
    start_validity_date: str | datetime | None = None,
) -> tuple[str, str, dict]:
    """
    .. warning::
        DO NOT CHANGE THIS FUNCTION. IT IS USED TO ENFORCE A STANDARD WAY OF
        NAMING THE RUNS, EXPERIMENTS AND BASIC TAGS

    Parameters
    ----------
    site : str
        Full windfarm name
    locations : str
        Full Turbine name
    output_name : str
        Name of the output parameter. This is the name of the signature output
        column, which is usually the target column name + "_pred".
    start_validity_date: str | datetime
        Start of validity of the model

    Returns
    -------
    tuple[str, str, dict]
        The experiment name, run name and tags in a standardised way.
    """
    experiment_name = site.lower()
    output_name = output_name.split("_pred", 1)[0]
    run_name = "_".join(
        [
            output_name,
            datetime.now().strftime("%Y-%m-%d-%H:%M"),
        ]
    )
    start_validity_date = parse_datetime_to_string(start_validity_date)

    tags = {
        "site": site,
        "locations": str(locations),
        "training_date": datetime.now().strftime("%Y.%m.%d"),
        "start_validity_date": start_validity_date,
    }
    return experiment_name, run_name, tags


@task
def balance_inputs_outputs(
    input_df: pd.DataFrame, target_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Drop nan values in both input and output and ensure they are in balance in
    terms of length.

    Parameters
    ----------
    input_df : pd.DataFrame
        The dataframe of the input data
    target_df : pd.DataFrame
        The dataframe of the output data
    """
    combined_df = pd.concat([input_df, target_df], axis=1)
    combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
    cleaned_combined_df = combined_df.dropna()
    input_cleaned = cleaned_combined_df[input_df.columns]
    output_cleaned = cleaned_combined_df[target_df.columns]
    return input_cleaned, output_cleaned


@task
def log_full_config(
    config: dict,
    config_path: Union[str, Path],
):
    """
    Logs all used conf files to MLflow as artifacts. This doesn't log the yaml
    files from the config folder. Instead it temporarily saves the each key of
    the config dictionary and logs it as an artifact, then deletes it.

    Parameters
    ----------
    config : dict
        The conf dictionary with all training configurations.
    """
    config_path = Path(config_path)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)
    mlflow.log_artifact(str(config_path), artifact_path="config")
    os.unlink(config_path)
