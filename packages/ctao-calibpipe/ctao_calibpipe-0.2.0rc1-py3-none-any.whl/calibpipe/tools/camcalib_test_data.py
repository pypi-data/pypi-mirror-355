"""Utility tool to produce test data for the camera calibration tools in the calibpipe package."""


import astropy.units as u
import yaml
from astropy.time import Time
from ctapipe.core import Tool, run_tool
from ctapipe.core.traits import (
    Bool,
    CaselessStrEnum,
    CInt,
    List,
    Path,
    Set,
    Unicode,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from ctapipe.tools.calculate_pixel_stats import PixelStatisticsCalculatorTool
from ctapipe.tools.process import ProcessorTool
from traitlets.config.loader import Config

__all__ = [
    "CamCalibTestDataTool",
]


class CamCalibTestDataTool(Tool):
    """Utility tool to produce test data for the camera calibration."""

    name = "calibpipe-produce-camcalib-test-data"

    description = "Produce test data for the camera calibration tools."

    examples = """
    To produce the test data for the camera calibration tools, you need to provide the input files
    for the pedestal and flatfield events, as well as the configuration files (see examples
    in the calibpipe documentation) for processing these events and aggregating the statistics.
    The timestamp of the events will be set to a realistic value based on the
    reference time and trigger rate defined in the tool. The output files will be created in the
    specified output directory, with the prefix defined in the configuration.

    Run with the following command to produce the test data:

    > calibpipe-produce-camcalib-test-data \\
        --pedestal pedestal_events.simtel.gz \\
        --flatfield flatfield_events.simtel.gz \\
        --output-dir ./output \\
        --CamCalibTestDataTool.process_pedestal_config ctapipe_process_pedestal.yaml \\
        --CamCalibTestDataTool.process_flatfield_config ctapipe_process_flatfield.yaml \\
        --CamCalibTestDataTool.agg_stats_pedestal_image_config ctapipe_calculate_pixel_stats_pedestal_image.yaml \\
        --CamCalibTestDataTool.agg_stats_flatfield_image_config ctapipe_calculate_pixel_stats_flatfield_image.yaml \\
        --CamCalibTestDataTool.agg_stats_flatfield_peak_time_config ctapipe_calculate_pixel_stats_flatfield_peak_time.yaml \\
        --CamCalibTestDataTool.prefix calibpipe_vX.Y.Z_statsagg \\
    """

    pedestal_input_url = Path(
        help="Simtel input file for pedestal events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    flatfield_input_url = Path(
        help="Simtel input file for flatfield events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    process_pedestal_config = Path(
        help="Path to the configuration file for processing pedestal events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    process_flatfield_config = Path(
        help="Path to the configuration file for processing flatfield events",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_pedestal_image_config = Path(
        help="Path to the configuration file for aggregating pedestal image statistics",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_flatfield_image_config = Path(
        help="Path to the configuration file for aggregating flatfield image statistics",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    agg_stats_flatfield_peak_time_config = Path(
        help="Path to the configuration file for aggregating flatfield peak time statistics",
        allow_none=False,
        exists=True,
        directory_ok=False,
        file_ok=True,
    ).tag(config=True)

    allowed_tels = Set(
        trait=CInt(),
        default_value=None,
        allow_none=True,
        help=(
            "List of allowed telescope IDs, others will be ignored. If None, all "
            "telescopes in the input stream will be included. Requires the "
            "telescope IDs to match between the groups of the monitoring file."
        ),
    ).tag(config=True)

    prefix = Unicode(
        default_value="statsagg",
        allow_none=False,
        help="Prefix to be used for the output files of the statistics aggregation",
    ).tag(config=True)

    aggregation_modes = List(
        trait=CaselessStrEnum(["single_chunk", "same_chunks", "different_chunks"]),
        default_value=["single_chunk", "same_chunks", "different_chunks"],
        allow_none=False,
        help=(
            "List of aggregation modes for the pixel statistics. "
            "Options are: 'single_chunk', 'same_chunks', 'different_chunks'. "
            "If 'single_chunk' is selected, all monitoring groups are aggregated in a single chunk. "
            "If 'same_chunks' is selected, all monitoring groups are aggregated in the same chunks. "
            "If 'different_chunks' is selected, each monitoring groups are aggregated in different chunks."
        ),
    ).tag(config=True)

    skip_r1_calibration = Bool(
        default_value=True,
        help=(
            "If True (default), skip the R1 calibration step in the simtel event source. "
            "This is useful for testing and validation purposes of the camera calibration routines. "
        ),
    ).tag(config=True)

    output_dir = Path(
        help="Directory to store the output files",
        allow_none=False,
        exists=True,
        directory_ok=True,
        file_ok=False,
    ).tag(config=True)

    aliases = {
        ("p", "pedestal"): "CamCalibTestDataTool.pedestal_input_url",
        ("f", "flatfield"): "CamCalibTestDataTool.flatfield_input_url",
        ("o", "output-dir"): "CamCalibTestDataTool.output_dir",
    }

    # Define the group in the DL1 file for the pedestal and flatfield images
    IMAGE_TEL_GROUP = "/dl1/event/telescope/images/"
    # Define the group in the monitoring file
    MONITORING_TEL_GROUP = "/dl1/monitoring/telescope/"
    # Define reference time and trigger rate for the tests. These values
    # are used to create realistic timestamps for the aggregated chunks.
    REFERENCE_TIME = Time.now()
    REFERENCE_TRIGGER_RATE = 1000.0 * u.Hz

    def setup(self):
        """Set up the tool."""
        # Load the subarray description from the input files
        subarray_pedestal = SubarrayDescription.read(self.pedestal_input_url)
        subarray_flatfield = SubarrayDescription.read(self.flatfield_input_url)
        # Check if the subarray descriptions match
        if not subarray_pedestal.__eq__(subarray_flatfield):
            raise ValueError(
                "The subarray descriptions of the pedestal and flatfield input files do not match."
            )
        # Select a new subarray if the allowed_tels configuration is used
        self.subarray = (
            subarray_pedestal
            if self.allowed_tels is None
            else subarray_pedestal.select_subarray(self.allowed_tels)
        )
        # The monitoring groups and their configurations to be used in the tests
        self.monitoring_groups = {
            "pedestal_image": self.agg_stats_pedestal_image_config,
            "flatfield_image": self.agg_stats_flatfield_image_config,
            "flatfield_peak_time": self.agg_stats_flatfield_peak_time_config,
        }
        # Create a configuration suitable for the tests
        self.sim_argv = [
            "--SimTelEventSource.skip_calibration_events=False",
            f"--SimTelEventSource.skip_r1_calibration={self.skip_r1_calibration}",
        ]

    def start(self):
        """Iterate over the telescope IDs and calculate the camera calibration coefficients."""
        # Set the path to the simtel calibration events
        # Set the output file path for pedestal images
        pedestal_dl1_image_file = self.output_dir / "pedestal_events.dl1.h5"
        with open(self.process_pedestal_config) as yaml_file:
            pedestal_config = yaml.safe_load(yaml_file)
            pedestal_dl1_image_file = self._run_ctapipe_process_tool(
                self.pedestal_input_url, pedestal_dl1_image_file, pedestal_config
            )
        # Set the output file path for flatfield images
        flatfield_dl1_image_file = self.output_dir / "flatfield_events.dl1.h5"
        with open(self.process_flatfield_config) as yaml_file:
            flatfield_config = yaml.safe_load(yaml_file)
            flatfield_dl1_image_file = self._run_ctapipe_process_tool(
                self.flatfield_input_url, flatfield_dl1_image_file, flatfield_config
            )

        # Iterate over the telescope IDs and calculate the camera calibration coefficients
        for tel_id in self.subarray.tel_ids:
            for aggregation_mode in self.aggregation_modes:
                # Create the statistics aggregation file for the given aggregation mode
                # Default chunk duration for the statistics aggregation
                chunk_duration = 25.0 * u.s
                # Set the output file path for the statistics aggregation
                output_file = (
                    self.output_dir / f"{self.prefix}_{aggregation_mode}.dl1.h5"
                )
                # Loop over the monitoring groups and calculate pixel statistics
                for mon_group, mon_config in self.monitoring_groups.items():
                    # Set the input file path for the PixelStatisticsCalculator
                    dl1_image_file = (
                        pedestal_dl1_image_file
                        if mon_group == "pedestal_image"
                        else flatfield_dl1_image_file
                    )
                    # Get the standard configuration for the PixelStatisticsCalculator
                    with open(mon_config) as yaml_file:
                        pix_stats_config = yaml.safe_load(yaml_file)
                        # Set some additional parameters using cli arguments
                        cli_argv = [
                            f"--input_url={dl1_image_file}",
                            f"--output_path={output_file}",
                            "--overwrite",
                        ]
                        n_events = len(
                            read_table(
                                dl1_image_file,
                                path=f"{self.IMAGE_TEL_GROUP}tel_{tel_id:03d}",
                            )
                        )
                        # Modify the configuration for the specific chunk mode
                        if aggregation_mode == "single_chunk":
                            chunk_duration = 1000.0 * u.s
                            # Overwrite the chunk size for the specific aggregator
                            if mon_group == "flatfield_peak_time":
                                cli_argv.append(
                                    f"--PlainAggregator.chunk_size={n_events}"
                                )
                            else:
                                cli_argv.append(
                                    f"--SigmaClippingAggregator.chunk_size={n_events}"
                                )
                        elif aggregation_mode == "same_chunks":
                            chunk_duration = 100.0 * u.s
                            # Overwrite the chunk size for the specific aggregator
                            if mon_group == "flatfield_peak_time":
                                cli_argv.append(
                                    f"--PlainAggregator.chunk_size={n_events//10}"
                                )
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
                        run_tool(
                            PixelStatisticsCalculatorTool(
                                config=Config(pix_stats_config)
                            ),
                            argv=cli_argv,
                            cwd=self.output_dir,
                            raises=True,
                        )
                        # Overwrite timestamps in the output file to make them realistic
                        # Read the created statsagg table for the specific monitoring group
                        stats_aggregation_tab = read_table(
                            output_file,
                            path=f"{self.MONITORING_TEL_GROUP}{mon_group}/tel_{tel_id:03d}",
                        )
                        # Loop over the chunks and set the new timestamps
                        for chunk_nr in range(len(stats_aggregation_tab)):
                            stats_aggregation_tab["time_start"][chunk_nr] = (
                                self.REFERENCE_TIME
                                + (1 / self.REFERENCE_TRIGGER_RATE).to(u.s)
                                + chunk_nr * chunk_duration
                            )
                            stats_aggregation_tab["time_end"][chunk_nr] = (
                                self.REFERENCE_TIME + (chunk_nr + 1) * chunk_duration
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
                            f"{self.MONITORING_TEL_GROUP}{mon_group}/tel_{tel_id:03d}",
                            overwrite=True,
                        )

    def finish(self):
        """Shut down the tool."""
        self.log.info("Tool is shutting down")

    def _run_ctapipe_process_tool(self, input_data, output_file, config):
        """Produce the DL1A file containing the images."""
        # Run the ProcessorTool to create images
        run_tool(
            ProcessorTool(config=Config(config)),
            argv=[
                f"--input={input_data}",
                f"--output={output_file}",
                "--overwrite",
            ]
            + self.sim_argv,
        )
        return output_file


def main():
    # Run the tool
    tool = CamCalibTestDataTool()
    tool.run()


if __name__ == "main":
    main()
