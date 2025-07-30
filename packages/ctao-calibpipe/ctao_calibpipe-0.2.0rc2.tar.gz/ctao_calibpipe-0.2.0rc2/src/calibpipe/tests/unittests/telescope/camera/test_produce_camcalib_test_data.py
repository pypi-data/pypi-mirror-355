#!/usr/bin/env python3
"""
Test calibpipe-produce-camcalib-test-data tool
"""

from pathlib import Path

from calibpipe.tools.camcalib_test_data import CamCalibTestDataTool
from ctapipe.core import run_tool

# Get the path to the configuration files
CONFIG_PATH = Path(__file__).parent.joinpath(
    "../../../../../../docs/source/examples/telescope/camera/configuration/"
)
# Get the path to the calibration events
DATA_PATH = Path(__file__).parent.joinpath("../../../data/telescope/camera/")


def test_produce_camcalib_test_data():
    """Test the calibpipe-produce-camcalib-test-data tool"""
    # Get the pedestal and flatfield simtel files
    pedestal_simtel_file = DATA_PATH.joinpath("pedestal_LST_dark.simtel.gz")
    flatfield_simtel_file = DATA_PATH.joinpath("flatfield_LST_dark.simtel.gz")
    # Run the tool with the configuration and the input files
    assert (
        run_tool(
            CamCalibTestDataTool(),
            argv=[
                f"--CamCalibTestDataTool.pedestal_input_url={pedestal_simtel_file}",
                f"--CamCalibTestDataTool.flatfield_input_url={flatfield_simtel_file}",
                f"--CamCalibTestDataTool.output_dir={DATA_PATH}",
                f"--CamCalibTestDataTool.process_pedestal_config={CONFIG_PATH.joinpath('ctapipe_process_pedestal.yaml')}",
                f"--CamCalibTestDataTool.process_flatfield_config={CONFIG_PATH.joinpath('ctapipe_process_flatfield.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_pedestal_image_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_pedestal_image.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_flatfield_image_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_flatfield_image.yaml')}",
                f"--CamCalibTestDataTool.agg_stats_flatfield_peak_time_config={CONFIG_PATH.joinpath('ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml')}",
            ],
            cwd=DATA_PATH,
            raises=True,
        )
        == 0
    )
