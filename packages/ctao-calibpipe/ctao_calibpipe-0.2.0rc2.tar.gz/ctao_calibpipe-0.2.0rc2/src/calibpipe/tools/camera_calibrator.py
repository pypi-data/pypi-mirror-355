"""Calculate camera calibration coefficients using the FFactor method."""

from collections import defaultdict

import astropy.units as u
import h5py
import numpy as np
from astropy.table import Column, Table
from ctapipe.core import Tool
from ctapipe.core.traits import (
    AstroQuantity,
    Bool,
    CInt,
    Float,
    Int,
    List,
    Path,
    Set,
    classes_with_traits,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table, write_table
from ctapipe.monitoring import ChunkInterpolator, StdOutlierDetector

__all__ = [
    "CameraCalibratorTool",
    "NpeStdOutlierDetector",
    "StatisticsInterpolator",
    "PedestalImageInterpolator",
    "FlatfieldImageInterpolator",
    "FlatfieldPeakTimeInterpolator",
]


# TODO These interpolator classes are temporary and should be migrated to or adjusted in ctapipe once interface with DataPipe is defined
# start_time and end_time should be renamed to time_start and time_end
class StatisticsInterpolator(ChunkInterpolator):
    """Interpolator for statistics tables."""

    required_columns = frozenset(["start_time", "end_time", "mean", "median", "std"])
    expected_units = {"mean": None, "median": None, "std": None}


class PedestalImageInterpolator(StatisticsInterpolator):
    """Interpolator for pedestal image tables."""

    telescope_data_group = "/dl1/monitoring/telescope/pedestal_image"


class FlatfieldImageInterpolator(StatisticsInterpolator):
    """Interpolator for flatfield image tables."""

    telescope_data_group = "/dl1/monitoring/telescope/flatfield_image"


class FlatfieldPeakTimeInterpolator(StatisticsInterpolator):
    """Interpolator for flatfield peak time tables."""

    telescope_data_group = "/dl1/monitoring/telescope/flatfield_peak_time"


class NpeStdOutlierDetector(StdOutlierDetector):
    """
    Detect outliers based on the deviation from the expected standard deviation of the number of photoelectrons.

    The clipping interval to set the thresholds for detecting outliers is computed by multiplying
    the configurable factors and the expected standard deviation of the number of photoelectrons. The
    expected standard deviation of the number of photoelectrons is calculated based on the median number
    of photoelectrons and the number of events.
    """

    n_events = Int(
        default_value=2500,
        help="Number of events used for the chunk-wise aggregation of the statistic values of the calibration data.",
    ).tag(config=True)

    relative_qe_dispersion = Float(
        0.07,
        help="Relative (effective) quantum efficiency dispersion of PMs over the camera",
    ).tag(config=True)

    linear_noise_coeff = List(
        trait=Float(),
        default_value=[1.79717813, 1.72458305],
        minlen=1,
        maxlen=2,
        help=(
            "Linear noise coefficients [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    linear_noise_offset = List(
        trait=Float(),
        default_value=[0.0231544, -0.00162036639],
        minlen=1,
        maxlen=2,
        help=(
            "Linear noise offsets [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    quadratic_noise_coeff = List(
        trait=Float(),
        default_value=[0.000499670969, 0.00142218],
        minlen=1,
        maxlen=2,
        help=(
            "Quadratic noise coefficients [high gain, low gain] or [single gain] obtained with a fit of the std of the "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    quadratic_noise_offset = List(
        trait=Float(),
        default_value=[0.0000249034290, 0.0001207],
        minlen=1,
        maxlen=2,
        help=(
            "Quadratic noise offsets [high gain, low gain] or [single gain] obtained with a fit of the std of the LST-1 "
            "LST-1 filter scan taken on 2023/05/10."
        ),
    ).tag(config=True)

    def __call__(self, column):
        r"""
        Detect outliers based on the deviation from the expected standard deviation of the number of photoelectrons.

        The clipping interval to set the thresholds for detecting outliers is computed by multiplying
        the configurable factors and the expected standard deviation of the number of photoelectrons
        (npe) over the camera. The expected standard deviation of the estimated npe is given by
        ``std_pe_mean = \frac{std_npe}{\sqrt{n_events + (relative_qe_dispersion \cdot npe)^2}}`` where the
        relative_qe_dispersion is mainly due to different detection QE among PMs. However, due to
        the systematics correction associated to the B term, a linear and quadratic noise component
        must be added, these components depend on the sample statistics (n_events).

        Parameters
        ----------
        column : astropy.table.Column
            Column of the calculated the number of photoelectrons using the chunk-wise aggregated statistic values
            of the calibration data of shape (n_entries, n_channels, n_pixels).

        Returns
        -------
        outliers : np.ndarray of bool
            The mask of outliers of shape (n_entries, n_channels, n_pixels) based on the deviation
            from the expected standard deviation of the number of photoelectrons.
        """
        # Calculate the median number of photoelectrons
        npe_median = np.nanmedian(column, axis=2)
        # Calculate the basic variance
        basic_variance = (
            npe_median / self.n_events + (self.relative_qe_dispersion * npe_median) ** 2
        )
        # Calculate the linear noise term
        linear_term = (
            self.linear_noise_coeff / (np.sqrt(self.n_events))
            + self.linear_noise_offset
        )
        # Calculate the quadratic noise term
        quadratic_term = (
            self.quadratic_noise_coeff / (np.sqrt(self.n_events))
            + self.quadratic_noise_offset
        )
        # Calculate the added variance
        added_variance = (linear_term * npe_median) ** 2 + (
            quadratic_term * npe_median
        ) ** 2
        # Calculate the total standard deviation of the number of photoelectrons
        npe_std = np.sqrt(basic_variance + added_variance)
        # Detect outliers based on the deviation of the standard deviation distribution
        deviation = column - npe_median[:, :, np.newaxis]
        outliers = np.logical_or(
            deviation < self.std_range_factors[0] * npe_std[:, :, np.newaxis],
            deviation > self.std_range_factors[1] * npe_std[:, :, np.newaxis],
        )
        return outliers


class CameraCalibratorTool(Tool):
    """Calculate camera calibration coefficients using the FFactor method."""

    name = "calibpipe-calculate-camcalib-coefficients"
    description = "Calculate camera calibration coefficients using the FFactor method"

    examples = """
    To calculate camera calibration coefficients using the FFactor method, run:

    > calibpipe-calculate-camcalib-coefficients --input_url monitoring.h5 --overwrite
    """

    input_url = Path(
        help="CTAO HDF5 files for DL1 calibration monitoring",
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

    timestamp_tolerance = AstroQuantity(
        default_value=u.Quantity(1.0, u.second),
        physical_type=u.physical.time,
        help="Time difference in seconds to consider two timestamps equal.",
    ).tag(config=True)

    faulty_pixels_fraction = Float(
        default_value=0.1,
        allow_none=True,
        help="Minimum fraction of faulty camera pixels to identify regions of trouble.",
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    systematic_correction_path = Path(
        default_value=None,
        allow_none=True,
        exists=True,
        directory_ok=False,
        help=(
            "Temp Fix: Path to systematic correction file "
            "for additional noise component that is proportional to the signal amplitude "
        ),
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    squared_excess_noise_factor = Float(
        1.222, help="Temp Fix: Excess noise factor squared: 1+ Var(gain)/Mean(Gain)**2"
    ).tag(config=True)

    # TODO These parameters are temporary and should be read from the metadata
    window_width = Int(
        12,
        help="Temp Fix: Width of the window used for the image extraction",
    ).tag(config=True)

    overwrite = Bool(help="Overwrite output file if it exists").tag(config=True)

    aliases = {
        ("i", "input_url"): "CameraCalibratorTool.input_url",
    }

    flags = {
        "overwrite": (
            {"CameraCalibratorTool": {"overwrite": True}},
            "Overwrite existing files",
        ),
    }

    classes = classes_with_traits(NpeStdOutlierDetector)

    # Define the group in the monitoring file
    MONITORING_TEL_GROUP = "/dl1/monitoring/telescope/"

    def setup(self):
        """Set up the tool.

        - Set up the subarray.
        - Load the systematic correction term B.
        - Configure the outlier detector for the expected standard deviation of the number of photoelectrons.
        """
        # Load the subarray description from the input file
        subarray = SubarrayDescription.from_hdf(self.input_url)
        # Select a new subarray if the allowed_tels configuration is used
        self.subarray = (
            subarray
            if self.allowed_tels is None
            else subarray.select_subarray(self.allowed_tels)
        )
        # Load systematic correction term B
        self.quadratic_term = 0
        if self.systematic_correction_path is not None:
            with h5py.File(self.systematic_correction_path, "r") as hf:
                self.quadratic_term = np.array(hf["B_term"])
        # Load the outlier detector for the expected standard deviation of the number of photoelectrons
        if "NpeStdOutlierDetector" in self.config:
            self.log.info(
                "Applying outlier detection 'NpeStdOutlierDetector' "
                "based on the deviation from the expected standard "
                "deviation of the number of photoelectrons."
            )
            self.outlier_detector = NpeStdOutlierDetector(
                parent=self, subarray=self.subarray
            )
        else:
            self.log.info(
                "No outlier detection applied. 'NpeStdOutlierDetector' not in config."
            )
            self.outlier_detector = None

        # Instantiate the chunk interpolators for each table
        self.pedestal_image_interpolator = PedestalImageInterpolator()
        self.flatfield_image_interpolator = FlatfieldImageInterpolator()
        self.flatfield_peak_time_interpolator = FlatfieldPeakTimeInterpolator()

    def start(self):
        """Iterate over the telescope IDs and calculate the camera calibration coefficients."""
        self.camcalib_table = {}
        # Iterate over the telescope IDs and calculate the camera calibration coefficients
        for tel_id in self.subarray.tel_ids:
            # Read the tables from the monitoring file requiring all tables to be present
            calibration_tables = {
                name: read_table(
                    self.input_url,
                    f"{self.MONITORING_TEL_GROUP}{name}/tel_{tel_id:03d}",
                )
                for name in ("pedestal_image", "flatfield_image", "flatfield_peak_time")
            }

            # Check if there is a single chunk for all the tables
            if all(len(table) == 1 for table in calibration_tables.values()):
                # If there is only a single chunk, set the unique timestamps to the start time
                unique_timestamps = [
                    min(
                        calibration_tables["pedestal_image"]["time_start"][0],
                        calibration_tables["flatfield_image"]["time_start"][0],
                    )
                ]
            else:
                # Get the unique timestamps from the tables
                unique_timestamps = self._get_unique_timestamps(
                    *calibration_tables.values()
                )
                # Process the tables and interpolate the data
                for name, interpolator in (
                    ("pedestal_image", self.pedestal_image_interpolator),
                    ("flatfield_image", self.flatfield_image_interpolator),
                    ("flatfield_peak_time", self.flatfield_peak_time_interpolator),
                ):
                    calibration_tables[name] = self._process_table(
                        tel_id,
                        calibration_tables[name],
                        interpolator,
                        unique_timestamps,
                    )

            # Concatenate the outlier masks
            outlier_mask = np.logical_or.reduce(
                [
                    np.isnan(table["median"].data)
                    for table in calibration_tables.values()
                ]
            )

            # Extract calibration coefficients with F-factor method
            # Calculate the signal
            signal = (
                calibration_tables["flatfield_image"]["median"].data
                - calibration_tables["pedestal_image"]["median"].data
            )
            # Calculate the gain with the excess noise factor must be known from elsewhere
            gain = (
                np.divide(
                    calibration_tables["flatfield_image"]["std"].data ** 2
                    - calibration_tables["pedestal_image"]["std"].data ** 2,
                    self.squared_excess_noise_factor * signal,
                )
                - self.quadratic_term**2 * signal / self.squared_excess_noise_factor
            )

            # Calculate the number of photoelectrons
            n_pe = np.divide(signal, gain)
            # Absolute gain calibration
            npe_median = np.nanmedian(n_pe, axis=2)

            data, units = {}, {}
            # Set the time column to the unique timestamps
            data["time"] = unique_timestamps
            data["factor"] = np.divide(npe_median[:, :, np.newaxis], signal)
            # Pedestal offset
            # TODO: read window_width from metadata
            data["pedestal_offset"] = (
                calibration_tables["pedestal_image"]["median"].data / self.window_width
            )
            units["pedestal_offset"] = calibration_tables["pedestal_image"][
                "median"
            ].unit
            # Relative time calibration
            median_arrival_time = np.nanmedian(
                calibration_tables["flatfield_peak_time"]["median"].data, axis=2
            )
            data["time_shift"] = (
                calibration_tables["flatfield_peak_time"]["median"].data
                - median_arrival_time[:, :, np.newaxis]
            )
            units["time_shift"] = calibration_tables["flatfield_peak_time"][
                "median"
            ].unit

            # Apply outlier detection if selected
            if self.outlier_detector is not None:
                # Create npe outlier mask
                npe_outliers = self.outlier_detector(Column(data=n_pe, name="n_pe"))
                # Stack the outlier masks with the npe outlier mask
                outlier_mask = np.logical_or(
                    outlier_mask,
                    npe_outliers,
                )
            # Append the column of the new outlier mask
            data["outlier_mask"] = outlier_mask
            # Check if the camera has two gain channels
            if outlier_mask.shape[1] == 2:
                # Combine the outlier mask of both gain channels
                outlier_mask = np.logical_or.reduce(outlier_mask, axis=1)
            # Calculate the fraction of faulty pixels over the camera
            faulty_pixels = (
                np.count_nonzero(outlier_mask, axis=-1) / np.shape(outlier_mask)[-1]
            )
            # Check for valid chunks if the predefined threshold ``faulty_pixels_fraction``
            # is not exceeded and append the is_valid column
            data["is_valid"] = faulty_pixels < self.faulty_pixels_fraction

            # Create the table for the camera calibration coefficients
            self.camcalib_table[tel_id] = Table(data, units=units)

    def finish(self):
        """Write the camera calibration coefficients to the output file."""
        # Overwrite the subarray description in the file if overwrite is selected
        self.subarray.to_hdf(self.input_url, overwrite=self.overwrite)
        self.log.info(
            "Subarray description was overwritten in '%s'",
            self.input_url,
        )
        # Write the camera calibration coefficients and their outlier mask
        # to the output file for each selected telescope
        for tel_id in self.subarray.tel_ids:
            write_table(
                self.camcalib_table[tel_id],
                self.input_url,
                f"{self.MONITORING_TEL_GROUP}camera_calibration/tel_{tel_id:03d}",
                overwrite=self.overwrite,
            )
            self.log.info(
                "DL1 monitoring data was stored in '%s' under '%s'",
                self.input_url,
                f"{self.MONITORING_TEL_GROUP}camera_calibration/tel_{tel_id:03d}",
            )
        self.log.info("Tool is shutting down")

    def _get_unique_timestamps(
        self, pedestal_image_table, flatfield_image_table, flatfield_peak_time_table
    ):
        """
        Extract unique timestamps from the given tables.

        This method collects the start and end timestamps from the provided
        chunks in the pedestal_image, flatfield_image, and flatfield_peak_time
        tables. It then sorts the timestamps and filters them based on the
        specified timestamp tolerance.

        Parameters
        ----------
        pedestal_image_table : astropy.table.Table
            Table containing pedestal image data.
        flatfield_image_table : astropy.table.Table
            Table containing flatfield image data.
        flatfield_peak_time_table : astropy.table.Table
            Table containing flatfield peak time data.

        Returns
        -------
        unique_timestamps : astropy.time.Time
            Unique timestamps sorted and filtered based on the timestamp tolerance.
        """
        # Collect all start and end times in MJD (days)
        timestamps = []
        for mon_table in (
            pedestal_image_table,
            flatfield_image_table,
            flatfield_peak_time_table,
        ):
            # Append timestamps from the start and end of chunks
            timestamps.append(mon_table["time_start"])
            timestamps.append(mon_table["time_end"])
        # Sort the timestamps
        timestamps = np.concatenate(timestamps)
        timestamps.sort()
        # Filter the timestamps based on the timestamp tolerance
        unique_timestamps = [timestamps[-1]]
        for t in reversed(timestamps[:-1]):
            if (unique_timestamps[-1] - t) > self.timestamp_tolerance:
                unique_timestamps.append(t)
        unique_timestamps.reverse()
        return unique_timestamps

    def _process_table(self, tel_id, table, interpolator, unique_timestamps):
        """
        Process the input table.

        This method processes the input table by renaming columns,
        adjusting the first timestamp, setting outliers to NaNs,
        and applying chunk interpolation.

        Parameters
        ----------
        tel_id : int
            Telescope ID.
        table : astropy.table.Table
            Table containing calibration data (pedestal, flatfield, or time correction).
        interpolator : callable
            Interpolation function to use.
        unique_timestamps : list
            List of unique timestamps for interpolation.

        Returns
        -------
        Table
            Processed table with interpolated data.
        """
        # TODO Rename columns in the tables. Do it in the interpolator.
        table.rename_column("time_start", "start_time")
        table.rename_column("time_end", "end_time")
        # Check if first timestamp is within the timestamp tolerance
        if (table["start_time"][0] - unique_timestamps[0]) < self.timestamp_tolerance:
            # Set the first timestamp to the first unique timestamp
            table["start_time"][0] = unique_timestamps[0]
        # Set outliers to NaNs
        for col in ["mean", "median", "std"]:
            table[col][table["outlier_mask"].data] = np.nan
        # Register the table with the interpolator
        interpolator.add_table(tel_id, table)
        # Interpolate data at the unique timestamps
        data = defaultdict(list)
        for time in unique_timestamps:
            data_interpolated = interpolator(tel_id, time)
            for col in ("mean", "median", "std"):
                # Interpolator returns np.nan if the requested time is outside the range.
                # In this case, we set the data to NaN for all channels and pixels
                # to avoid the stack operation below to fail.
                if np.isscalar(data_interpolated[col]) and np.isnan(
                    data_interpolated[col]
                ):
                    data_interpolated[col] = np.full(table[col][0].shape, np.nan)
                data[col].append(data_interpolated[col])
        # Stack the data to a numpy array
        for col in ("mean", "median", "std"):
            data[col] = np.stack(data[col], axis=0)
        return Table(data)


def main():
    # Run the tool
    tool = CameraCalibratorTool()
    tool.run()


if __name__ == "main":
    main()
