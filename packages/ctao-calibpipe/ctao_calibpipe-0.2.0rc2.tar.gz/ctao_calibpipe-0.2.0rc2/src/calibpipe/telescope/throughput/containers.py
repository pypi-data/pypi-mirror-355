"""Containers to keep optical throughput data and metadata."""

import datetime

import numpy as np
from ctapipe.core import Container, Field

# UNIX_TIME_ZERO value corresponds to "epoch" special time from PostgreSQL documentation:
# https://www.postgresql.org/docs/current/datatype-datetime.html#DATATYPE-DATETIME-SPECIAL-TABLE

UNIX_TIME_ZERO = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


class OpticalThoughtputContainer(Container):
    """Optical throughput calibration coefficient and analysis results for a single telescope."""

    optical_throughput_coefficient = Field(
        np.nan,
        "Optical throughput from the selected calibration method",
        type=np.float64,
        allow_none=False,
    )
    optical_throughput_coefficient_std = Field(
        np.nan,
        "Optical throughput from the selected calibration method",
        type=np.float64,
        allow_none=False,
    )
    method = Field(
        "None",
        "Calibration method used to fill optical_throughput_coefficient",
        type=str,
        allow_none=False,
    )
    validity_start = Field(
        UNIX_TIME_ZERO,
        description="Starting timestamp of validity for the selected throughput.",
        type=datetime.datetime,
        allow_none=False,
    )
    validity_end = Field(
        UNIX_TIME_ZERO,
        description="Ending timestamp of validity for the selected throughput.",
        type=datetime.datetime,
        allow_none=False,
    )
    obs_id = Field(
        -1,
        description="ID of the observation block for validity",
        type=np.int32,
        allow_none=False,
    )
    tel_id = Field(-1, description="Telescope ID", type=np.int32, allow_none=False)
    n_events = Field(
        0,
        description="Number of muon rings used to calculate the throughput",
        type=np.int32,
        allow_none=False,
    )
