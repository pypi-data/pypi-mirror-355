#!/usr/bin/env python3
"""
Test calibpipe-calculate-camcalib-coefficients tool
"""

from pathlib import Path

import numpy as np
import pytest
import yaml
from astropy import units as u
from astropy.time import Time
from calibpipe.tools.camera_calibrator import CameraCalibratorTool
from ctapipe.core import run_tool
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from ctapipe.tools.calculate_pixel_stats import PixelStatisticsCalculatorTool
from ctapipe.tools.process import ProcessorTool
from traitlets.config.loader import Config

# Get the path to the configuration files
CONFIG_PATH = Path(__file__).parent.joinpath(
    "../../../../../../docs/source/examples/telescope/camera/configuration/"
)
# Get the path to the calibration events
DATA_PATH = Path(__file__).parent.joinpath("../../../data/telescope/camera/")
# The telescope ID to be used in the tests
TEL_ID = 1
# Define the group in the monitoring file
MONITORING_TEL_GROUP = "/dl1/monitoring/telescope/"
# The monitoring groups to be used in the tests
MONITORING_GROUPS = ["pedestal_image", "flatfield_image", "flatfield_peak_time"]
# Define reference time and trigger rate for the tests. These values
# are used to create realistic timestamps for the aggregated chunks.
REFERENCE_TIME = Time.now()
REFERENCE_TRIGGER_RATE = 1000.0 * u.Hz
# Create a configuration suitable for the tests
SIM_ARGV = [
    "--SimTelEventSource.skip_calibration_events=False",
    "--SimTelEventSource.skip_r1_calibration=True",
]
# Simulated values for the tests for the different gain channels
# HG: High Gain, LG: Low Gain
EXPECTED_ADC_OFFSET = {"HG": 400, "LG": 400}
EXPECTED_DC2PE = {"HG": 0.015, "LG": 0.25}
EXPECTED_TIME_SHIFT = {"HG": 0.0, "LG": 0.0}
# Set different file prefixes and tolerances for the two statistic modes
#   - 'low_stats': 100 events per calibration type processed from simtel files to the final camcalib
#                 coefficients to ensure that the camcalib coefficients calculation works from DL0.
#                 Due to the low number of events, the tolerance for the coefficients is relatively high,
#                 since the statistics are not sufficient to calculate the coefficients with high precision.
#   - 'high_stats': 25000 events per calibration type already aggregated from simtel files via
#                 the 'CamCalibTestDataTool' and retrieved from MinIO. The final camcalib coefficients
#                 are calculated from the aggregated statistics files to test the correctness
#                 of the camcalib coefficients calculation within a restrictive tolerance.
FILE_PREFIX = {"low_stats": "statsagg_", "high_stats": "calibpipe_v0.2.0_statsagg_"}
DC2PE_TOLERANCE = {
    "low_stats": {"rtol": 0.25, "atol": 0.0},
    "high_stats": {"rtol": 0.02, "atol": 0.0},
}
ADC_OFFSET_TOLERANCE = {
    "low_stats": {"rtol": 0.0, "atol": 10.0},
    "high_stats": {"rtol": 0.0, "atol": 2.0},
}
TIME_SHIFT_TOLERANCE = {
    "low_stats": {"rtol": 0.0, "atol": 0.25},
    "high_stats": {"rtol": 0.0, "atol": 0.25},
}


@pytest.mark.order(1)
def test_produce_dl1_image_file():
    """
    Produce DL1A file containing the images of the calibration events.
    """
    # Set the path to the simtel calibration events
    for calibration_type in ["pedestal", "flatfield"]:
        simtel_file = DATA_PATH.joinpath(f"{calibration_type}_LST_dark.simtel.gz")
        # Set the output file path for pedestal images
        image_file = DATA_PATH.joinpath(f"{calibration_type}_events.dl1.h5")
        with open(
            CONFIG_PATH.joinpath(f"ctapipe_process_{calibration_type}.yaml")
        ) as yaml_file:
            config = yaml.safe_load(yaml_file)
            # Run the ProcessorTool to create pedestal images
            assert (
                run_tool(
                    ProcessorTool(config=Config(config)),
                    argv=[
                        f"--input={simtel_file}",
                        f"--output={image_file}",
                        "--overwrite",
                    ]
                    + SIM_ARGV,
                    cwd=DATA_PATH,
                )
                == 0
            )


@pytest.mark.order(2)
@pytest.mark.verifies_usecase("UC-120-2.21")
@pytest.mark.parametrize(
    "aggregation_mode",
    ["single_chunk", "same_chunks", "different_chunks"],
)
def test_stats_aggregation(aggregation_mode):
    """
    DL1 camera monitoring file containing the statistics aggregation for a given chunk mode.
    """
    # Set the output file path for the statistics aggregation
    output_file = DATA_PATH.joinpath(f"statsagg_{aggregation_mode}.dl1.h5")
    # Loop over the monitoring groups and calculate pixel statistics
    for mon_group in MONITORING_GROUPS:
        # Set the input file path for the PixelStatisticsCalculator
        dl1_image_file = (
            DATA_PATH.joinpath("pedestal_events.dl1.h5")
            if mon_group == "pedestal_image"
            else DATA_PATH.joinpath("flatfield_events.dl1.h5")
        )
        # Get the standard configuration for the PixelStatisticsCalculator
        with open(
            CONFIG_PATH.joinpath(f"ctapipe_calculate_pixel_stats_{mon_group}.yaml")
        ) as yaml_file:
            pix_stats_config = yaml.safe_load(yaml_file)
            # Set some additional parameters using cli arguments
            cli_argv = [
                f"--input_url={dl1_image_file}",
                f"--output_path={output_file}",
            ]
            n_events = len(
                read_table(
                    dl1_image_file,
                    path=f"/dl1/event/telescope/images/tel_{TEL_ID:03d}",
                )
            )
            # Modify the configuration for the specific chunk mode
            if aggregation_mode == "single_chunk":
                chunk_duration = 1000.0 * u.s
                # Use a single chunk size for all monitoring groups
                # Overwrite the chunk size for the specific aggregator
                if mon_group == "flatfield_peak_time":
                    cli_argv.append(f"--PlainAggregator.chunk_size={n_events}")
                else:
                    cli_argv.append(f"--SigmaClippingAggregator.chunk_size={n_events}")
            elif aggregation_mode == "same_chunks":
                chunk_duration = 100.0 * u.s
                # Overwrite the chunk size for the specific aggregators to have ten chunks
                if mon_group == "flatfield_peak_time":
                    cli_argv.append(f"--PlainAggregator.chunk_size={n_events//10}")
                else:
                    cli_argv.append(
                        f"--SigmaClippingAggregator.chunk_size={n_events//10}"
                    )
            elif aggregation_mode == "different_chunks":
                # Use different chunk sizes for each monitoring group
                if mon_group == "pedestal_image":
                    chunk_duration = 200.0 * u.s
                    cli_argv.append(
                        f"--SigmaClippingAggregator.chunk_size={2 * (n_events//10)}"
                    )
                elif mon_group == "flatfield_image":
                    chunk_duration = 100.0 * u.s
                    cli_argv.append(
                        f"--SigmaClippingAggregator.chunk_size={n_events//10}"
                    )
                elif mon_group == "flatfield_peak_time":
                    chunk_duration = 500.0 * u.s
                    cli_argv.append(
                        f"--PlainAggregator.chunk_size={5 * (n_events//10)}"
                    )

            # Run the PixelStatisticsCalculatorTool to calculate pixel statistics
            assert (
                run_tool(
                    PixelStatisticsCalculatorTool(config=Config(pix_stats_config)),
                    argv=cli_argv,
                    cwd=DATA_PATH,
                    raises=True,
                )
                == 0
            )
            # Overwrite timestamps in the output file to make them realistic
            # Read the created statsagg table for the specific monitoring group
            stats_aggregation_tab = read_table(
                output_file,
                path=f"{MONITORING_TEL_GROUP}{mon_group}/tel_{TEL_ID:03d}",
            )
            # Loop over the chunks and set the new timestamps
            for chunk_nr in range(len(stats_aggregation_tab)):
                stats_aggregation_tab["time_start"][chunk_nr] = (
                    REFERENCE_TIME
                    + (1 / REFERENCE_TRIGGER_RATE).to(u.s)
                    + chunk_nr * chunk_duration
                )
                stats_aggregation_tab["time_end"][chunk_nr] = (
                    REFERENCE_TIME + (chunk_nr + 1) * chunk_duration
                )
            # Set a different starting time (outside the default 1 second tolerance)
            # for the pedestal group if the mode is 'diffent_chunks'. This is to ensure
            # that the we can later test when the chunk interpolator is returning NaN values
            # for the first and last unique timestamps.
            if aggregation_mode == "different_chunks":
                if mon_group == "pedestal_image":
                    stats_aggregation_tab["time_start"][0] -= 2 * u.s
                    stats_aggregation_tab["time_end"][-1] += 2 * u.s
            # Overwrite the table in the output file
            write_table(
                stats_aggregation_tab,
                output_file,
                f"{MONITORING_TEL_GROUP}{mon_group}/tel_{TEL_ID:03d}",
                overwrite=True,
            )


# We are ignoring the warning about NaN slices, since we expect all values to be
# NaN for the first and last timestamps in the 'different_chunks' mode.
@pytest.mark.order(3)
@pytest.mark.verifies_usecase("UC-120-2.20")
@pytest.mark.parametrize(
    "statistic_mode",
    ["low_stats", "high_stats"],
)
@pytest.mark.filterwarnings("ignore:All-NaN slice encountered")
def test_calculate_camcalib_coeffs_tool(statistic_mode):
    """check camcalib coefficients calculation from dl1 camera monitoring data files"""
    # There are three different aggregation modes:
    #   - single_chunk: all monitoring groups are aggregated in a single chunk
    #   - same_chunks: all monitoring groups are aggregated in the same chunks
    #   - different_chunks: each monitoring group is aggregated in different chunks
    for aggregation_mode in ["single_chunk", "same_chunks", "different_chunks"]:
        # Set the path to the simtel pedestal events
        stats_aggregation_file = DATA_PATH.joinpath(
            f"{FILE_PREFIX[statistic_mode]}{aggregation_mode}.dl1.h5"
        )
        # Run the tool with the configuration and the input file
        assert (
            run_tool(
                CameraCalibratorTool(),
                argv=[
                    f"--input_url={stats_aggregation_file}",
                    "--overwrite",
                ],
                cwd=DATA_PATH,
                raises=True,
            )
            == 0
        )
        # Read subarray description from the created monitoring file
        subarray = SubarrayDescription.from_hdf(stats_aggregation_file)
        # Check for the selected telescope
        assert subarray.tel_ids[0] == TEL_ID
        # Read the camera calibration coefficients from the created monitoring file
        # and check that the calculated values are as expected.
        camcalib_coeffs = read_table(
            stats_aggregation_file,
            path=f"{MONITORING_TEL_GROUP}camera_calibration/tel_{TEL_ID:03d}",
        )
        for i in range(len(camcalib_coeffs)):
            if aggregation_mode == "different_chunks":
                # For the 'different_chunks' mode, we expect the first factor and pedestal
                # to be NaN, since the first timestamp is not valid for the pedestal group.
                if i == 0 or i == len(camcalib_coeffs) - 1:
                    # Check that the factor and time shift are NaN for the first and last timestamps
                    assert np.isnan(camcalib_coeffs["factor"][i]).all()
                    assert np.isnan(camcalib_coeffs["time_shift"][i]).all()
                    # Check that the outlier mask is all True for the first and last timestamps
                    assert camcalib_coeffs["outlier_mask"][i].all()
                    # Check that the is_valid flag is False for the first and last timestamps
                    assert not camcalib_coeffs["is_valid"][i]
                    # Check that the pedestal offsets are not NaN since the first and last timestamps
                    # are valid for the pedestal group.
                    for g, gain_channel in enumerate(["HG", "LG"]):
                        np.testing.assert_allclose(
                            np.nanmedian(camcalib_coeffs["pedestal_offset"][i][g]),
                            EXPECTED_ADC_OFFSET[gain_channel],
                            rtol=ADC_OFFSET_TOLERANCE[statistic_mode]["rtol"],
                            atol=ADC_OFFSET_TOLERANCE[statistic_mode]["atol"],
                            err_msg=(
                                f"Pedestal per sample values do not match expected values within "
                                f"a tolerance of {int(ADC_OFFSET_TOLERANCE[statistic_mode]['atol'])} ADC counts"
                            ),
                        )
                    continue
            # Check that the median of the calculated factor is close to the
            # simtel_dc2pe values for the corresponding gain channel.
            for g, gain_channel in enumerate(["HG", "LG"]):
                np.testing.assert_allclose(
                    np.nanmedian(camcalib_coeffs["factor"][i][g]),
                    EXPECTED_DC2PE[gain_channel],
                    rtol=DC2PE_TOLERANCE[statistic_mode]["rtol"],
                    atol=DC2PE_TOLERANCE[statistic_mode]["atol"],
                    err_msg=(
                        f"Factor coefficients do not match expected values within "
                        f"a tolerance of {int(DC2PE_TOLERANCE[statistic_mode]['rtol']*100)}%"
                    ),
                )
                # Check that the median of the calculated pedestal offset is close to the
                # simtel_pedestal_per_sample values for the corresponding gain channel.
                np.testing.assert_allclose(
                    np.nanmedian(camcalib_coeffs["pedestal_offset"][i][g]),
                    EXPECTED_ADC_OFFSET[gain_channel],
                    rtol=ADC_OFFSET_TOLERANCE[statistic_mode]["rtol"],
                    atol=ADC_OFFSET_TOLERANCE[statistic_mode]["atol"],
                    err_msg=(
                        f"Pedestal per sample values do not match expected values within "
                        f"a tolerance of {int(ADC_OFFSET_TOLERANCE[statistic_mode]['atol'])} ADC counts"
                    ),
                )
                # Check that the median of the calculated time shift is close to the
                # simtel_time_shift values for the corresponding gain channel.
                np.testing.assert_allclose(
                    np.nanmedian(camcalib_coeffs["time_shift"][i][g]),
                    EXPECTED_TIME_SHIFT[gain_channel],
                    rtol=TIME_SHIFT_TOLERANCE[statistic_mode]["rtol"],
                    atol=TIME_SHIFT_TOLERANCE[statistic_mode]["atol"],
                    err_msg=(
                        "Time shift values do not match expected values "
                        "within a tolerance of a quarter of a waveform sample"
                    ),
                )
            # Check that the is_valid flag is True for all timestamps
            assert camcalib_coeffs["is_valid"][i]


def test_npe_std_outlier_detector():
    """check camcalib coefficients calculation with the NpeStdOutlierDetector"""
    # Only consider the single_chunk aggregation mode for this test
    stats_aggregation_file = DATA_PATH.joinpath(
        "calibpipe_v0.2.0_statsagg_single_chunk.dl1.h5"
    )
    # Read the NpeStdOutlierDetector configuration from the YAML file
    with open(CONFIG_PATH.joinpath("npe_std_outlier_detector.yaml")) as yaml_file:
        npe_std_outlier_detector_config = yaml.safe_load(yaml_file)
        # Run the CameraCalibratorTool with the NpeStdOutlierDetector configuration
        assert (
            run_tool(
                CameraCalibratorTool(config=Config(npe_std_outlier_detector_config)),
                argv=[
                    f"--input_url={stats_aggregation_file}",
                    "--overwrite",
                ],
                cwd=DATA_PATH,
                raises=True,
            )
            == 0
        )
