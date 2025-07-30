# -*- coding: utf-8 -*-
"""Transform step for the data preprocessing. The functions defined in this file
serve as a template for the data preprocessing step in a Prefect flow.
Using Prefect is not a necessary requirement, and it is done here as an example
of how to use an orchestrator to manage ML workflows.

The main function to be used for the transformation of the dataframe is
``transform_flow``, which, if Prefect is used, should be decorated with the
@flow decorator. It works in combination with configuaration files. Specifically
for the transform step, the main configuration of interest is the
ingest.yaml file in which the specific processors to use, along with their
arguments can be specified. For each preprocessing step (e.g. removing nan
values) it is recommended to define a function in the misc.preprocessors file
and import it here. Otherwise directly defining the functions in the present
file can also work.
"""

from __future__ import annotations

import sys
from functools import partial
from typing import Callable

from prefect import task
from sklearn.pipeline import FunctionTransformer, Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from ..misc.preprocessors import *  # noqa: F401, F403 # pylint: disable=unused-wildcard-import, wildcard-import

scaler_name_dict = {
    "standardscaler": StandardScaler,
    "minmaxscaler": MinMaxScaler,
}


# pylint: disable=R0914, R0912
@task
def build_preprocessing_pipeline(
    transform_config: dict, preprocessors: list[Callable]
) -> Pipeline:
    """Create a preprocessing pipeline based on the tranform configuration and
    functions defined in misc.preprocessors.

    Parameters
    ----------
    transform_config : dict
        A dictionary containing the tranform configuration, with the
        preprocessing steps, and optionally a scaler specification.

    Returns
    -------
    Pipeline
        The preprocessing pipeline

    Raises
    ------
    NotImplementedError
        If a scaler order other than "first" or "last" is specified in the
        config
    NotImplementedError
        If a scaler type other than "standardscaler" or "minmaxscaler" is
        specified
    """
    steps = []

    scaler_config = transform_config.get("scaler", {})

    # Create a lookup map for preprocessors passed as arguments
    # Ensure preprocessors is not None before iterating
    passed_preprocessors_map: dict[str, Callable] = {}
    if preprocessors:
        for func_obj in preprocessors:
            if callable(func_obj) and hasattr(func_obj, "__name__"):
                passed_preprocessors_map[func_obj.__name__] = func_obj
            else:
                # Optionally, raise an error or warning for invalid items
                print(
                    f"Warning: Item {func_obj} in preprocessors list is not a "
                    "named callable and will be ignored."
                )

    current_module = sys.modules[__name__]
    for step in transform_config["steps"]:
        for func_name, args in step.items():
            func = None
            # 1. Try to get from passed_preprocessors_map
            if func_name in passed_preprocessors_map:
                func = passed_preprocessors_map[func_name]
            # 2. Else, try to get from the current module
            elif hasattr(current_module, func_name):
                func_candidate = getattr(current_module, func_name)
                if callable(func_candidate):
                    func = func_candidate

            if func is None:
                raise NameError(
                    f"Preprocessor function '{func_name}' not found. "
                    f"Searched in functions passed via 'preprocessors' argument"
                    f" and in module '{current_module.__name__}'."
                )
            wrapped = partial(func, **args) if isinstance(args, dict) else func
            tx = FunctionTransformer(wrapped, validate=False)
            steps.append((func_name, tx))

    if scaler_config:
        scaler_name = scaler_config["type"].lower()
        scaler_order = scaler_config["order"].lower()
        if scaler_name not in scaler_name_dict:
            raise NotImplementedError(
                f"Scaler type {scaler_config['type']} not recognized. "
                f"Available options: {list(scaler_name_dict.keys())}"
            )
        scaler = scaler_name_dict[
            scaler_name
        ]()  # () needed to instantiate the scaler
        if scaler_order == "first":
            # If the scaler is to be applied first, we add it at the beginning
            steps.insert(0, ("scaler", scaler))
        elif scaler_order == "last":
            # If the scaler is to be applied last, we add it at the end
            steps.append(("scaler", scaler))
        else:
            raise NotImplementedError(
                f"Scaler order {scaler_order} not recognized. "
                "Available options: 'first', 'last'"
            )
    pipeline = Pipeline(steps)
    pipeline.set_output(transform="pandas")
    return pipeline


# pylint: enable=R0914, R0912
