"""Tool for calculating of optical throughput and storing of the results in the DB."""

from os import path

import numpy as np
from astropy.table import QTable, vstack
from astropy.time import Time
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler
from calibpipe.telescope.throughput.containers import OpticalThoughtputContainer
from ctapipe.core import traits
from ctapipe.core.traits import CInt, Path, Set
from ctapipe.instrument import SubarrayDescription
from ctapipe.io import read_table
from traitlets import Float, Int, Unicode

from .basic_tool_with_db import BasicToolWithDB


class CalculateThroughputWithMuons(BasicToolWithDB):
    """Perform throughput calibration using muons for each telescope allowed in the EventSource."""

    name = traits.Unicode("ThroughputCalibration")
    description = __doc__

    input_url = Path(
        help="CTAO HDF5 files for DL1 calibration (muons).",
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

    # TODO: Write back to the DL1 monitoring file instead
    output_url = Path(
        "./OpticalThroughput.ecsv",
        help="Path to the output file where the optical throughput calibration will be saved",
        allow_none=False,
        directory_ok=True,
    ).tag(config=True)

    output_format = Unicode(
        "ascii.ecsv",
        help="Output files format",
        allow_none=False,
    ).tag(config=True)

    min_events = Int(
        default_value=0,
        help="Min number of muon events required to pass the cuts for throughput calculation",
    ).tag(config=True)

    min_ring_radius = Float(default_value=0.8, help="Minimum ring radius in deg").tag(
        config=True
    )

    max_ring_radius = Float(default_value=1.2, help="Maximum ring radius in deg").tag(
        config=True
    )

    min_impact_parameter = Float(
        default_value=0.2,
        help="Minimum impact parameter in mirror_radius fractional units",
    ).tag(config=True)

    max_impact_parameter = Float(
        default_value=0.9,
        help="Maximum impact parameter in mirror_radius fractional units",
    ).tag(config=True)

    ring_completeness_threshold = Float(
        default_value=0.3, help="Lower threshold for ring completeness"
    ).tag(config=True)

    ring_containment_threshold = Float(
        default_value=0.3, help="Lower threshold for ring containment"
    ).tag(config=True)

    intensity_ratio = Float(
        default_value=0.5,
        help="Ratio of the photons inside a given ring."
        " The ring is assumed to be in [radius - 0.5 * width, radius + 0.5 * width]",
    ).tag(config=True)

    TEL_GROUP = "/dl1/event/telescope"
    METHOD = "Muon Rings"

    def setup(self):
        """Read from the .h5 file necessary info and save it for further processing."""
        # Load the subarray description from the input file
        subarray = SubarrayDescription.from_hdf(self.input_url)
        # Select a new subarray if the allowed_tels configuration is used
        self.subarray = (
            subarray
            if self.allowed_tels is None
            else subarray.select_subarray(self.allowed_tels)
        )

        self.throughput_containers = {}

    def start(self):
        """
        Apply the cuts on the muon data and store the results in containers.

        Only the events that passed quality cuts provided by configuration are considered.
        Only events for which intensity fit converged, and parameters were not at the limit are considered.
        """
        for tel_id in self.subarray.tel_ids:
            muon_table = read_table(
                self.input_url,
                f"{self.TEL_GROUP}/muon/tel_{tel_id:03d}",
            )
            throughput_container = OpticalThoughtputContainer()
            trigger_table = read_table(
                self.input_url,
                f"{self.TEL_GROUP}/trigger",
            )
            start, end = trigger_table["time"].min(), trigger_table["time"].max()

            mask = (
                (muon_table["muonring_radius"] >= self.min_ring_radius)
                & (muon_table["muonring_radius"] <= self.max_ring_radius)
                & (muon_table["muonefficiency_impact"] >= self.min_impact_parameter)
                & (muon_table["muonefficiency_impact"] <= self.max_impact_parameter)
                & (
                    muon_table["muonparameters_completeness"]
                    >= self.ring_completeness_threshold
                )
                & (
                    muon_table["muonparameters_containment"]
                    >= self.ring_containment_threshold
                )
                & (muon_table["muonparameters_intensity_ratio"] >= self.intensity_ratio)
                & (muon_table["muonefficiency_is_valid"] != 0)
                & (muon_table["muonefficiency_parameters_at_limit"] != 1)
            )

            filtered_table = muon_table[mask]

            if len(filtered_table) > 0:
                throughput_container.tel_id = tel_id
                throughput_container.obs_id = filtered_table["obs_id"][0]
                throughput_container.method = self.METHOD
                throughput_container.optical_throughput_coefficient = np.mean(
                    filtered_table["muonefficiency_optical_efficiency"]
                )
                throughput_container.optical_throughput_coefficient_std = np.std(
                    filtered_table["muonefficiency_optical_efficiency"]
                )
                throughput_container.validity_start = Time(
                    start, format="mjd", scale="utc"
                ).to_datetime()
                throughput_container.validity_end = Time(
                    end, format="mjd", scale="utc"
                ).to_datetime()
                throughput_container.n_events = len(filtered_table)

            self.throughput_containers[tel_id] = throughput_container

    def finish(self):
        """Write the results to the output file and DB."""
        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            for tel_id, throughput_container in self.throughput_containers.items():
                self.log.info(
                    "Optical throughput for telescope %s is uploaded to CalibPipe DB "
                    "from the calibration method %s",
                    tel_id,
                    throughput_container.method,
                )

                # reference metadata is identical at the moment
                TableHandler.upload_data(throughput_container, None, connection)

        with CalibPipeDatabase(
            **self.database_configuration,
        ) as connection:
            self.output_url.parent.mkdir(parents=True, exist_ok=True)

            db_table = TableHandler.read_table_from_database(
                type(OpticalThoughtputContainer()), connection
            )

            if path.exists(self.output_url):
                try:
                    existing_table = QTable.read(
                        self.output_url, format=self.output_format
                    )
                    db_table_subset = db_table[:-1].copy()
                    # Convert 'validity_end' and 'validity_start' to Time objects, to be consistent with the existing table
                    db_table_subset["validity_end"] = Time(
                        db_table_subset["validity_end"], scale="utc"
                    )
                    db_table_subset["validity_start"] = Time(
                        db_table_subset["validity_start"], scale="utc"
                    )
                    combined_table = vstack(
                        [existing_table, db_table_subset], join_type="exact"
                    )
                    combined_table.write(
                        self.output_url, format=self.output_format, overwrite=True
                    )
                except Exception as e:
                    self.log.exception(
                        "Error reading or writing the existing .ecsv file: %s", e
                    )
            else:
                try:
                    # Need to properly handle datetime object for JSON serialization
                    db_table["validity_end"] = Time(
                        db_table["validity_end"], scale="utc"
                    )
                    db_table["validity_start"] = Time(
                        db_table["validity_start"], scale="utc"
                    )
                    db_table.write(
                        self.output_url, format=self.output_format, overwrite=True
                    )
                except Exception as e:
                    self.log.exception("Error writing the .ecsv file: %s", e)
                    raise


def main():
    """Run the app."""
    tool = CalculateThroughputWithMuons()
    tool.run()
