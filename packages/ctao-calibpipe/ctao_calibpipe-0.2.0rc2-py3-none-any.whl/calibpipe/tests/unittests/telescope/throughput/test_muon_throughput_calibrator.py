from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
import yaml
from astropy.table import QTable
from astropy.time import Time
from calibpipe.database.connections import CalibPipeDatabase
from calibpipe.database.interfaces import TableHandler
from calibpipe.telescope.throughput.containers import (
    OpticalThoughtputContainer,
)
from calibpipe.tools.muon_throughput_calculator import CalculateThroughputWithMuons
from traitlets.config.loader import Config


class TestMuonThroughputCalibration:
    config_path = Path(__file__).parent.joinpath(
        "../../../../../../docs/source/examples/telescope/throughput/configuration/"
    )
    db_config_path = Path(__file__).parent.joinpath(
        "../../../../../../docs/source/examples/utils/configuration/"
    )
    data_path = Path(__file__).parent.joinpath("../../../data/telescope/throughput/")

    with open(config_path.joinpath("throughput_muon_configuration.yaml")) as yaml_file:
        data = yaml.safe_load(yaml_file)
        data["CalculateThroughputWithMuons"]["output_url"] = data_path.joinpath(
            "OpticalThroughput.ecsv"
        )

    input_empty_muon_table = data_path.joinpath("empty_muon_table.h5")
    input_good_muon_table_lst = data_path.joinpath("lst_muon_table.h5")

    @pytest.mark.muon()
    def test_empty_data(self):
        self.data["CalculateThroughputWithMuons"][
            "input_url"
        ] = self.input_empty_muon_table
        test_calculate_throughput_muon_tool = CalculateThroughputWithMuons(
            config=Config(self.data)
        )

        test_calculate_throughput_muon_tool.setup()
        test_calculate_throughput_muon_tool.start()

        result = test_calculate_throughput_muon_tool.throughput_containers

        assert np.isnan(result[1]["optical_throughput_coefficient"])
        assert np.isnan(result[1]["optical_throughput_coefficient_std"])
        assert result[1]["method"] == "None"

    @pytest.mark.muon()
    def test_muon_data(self):
        self.data["CalculateThroughputWithMuons"][
            "input_url"
        ] = self.input_good_muon_table_lst
        test_calculate_throughput_muon_tool = CalculateThroughputWithMuons(
            config=Config(self.data)
        )

        test_calculate_throughput_muon_tool.setup()
        test_calculate_throughput_muon_tool.start()

        containers = test_calculate_throughput_muon_tool.throughput_containers

        assert containers is not None

        expected_values = {
            "optical_throughput_coefficient": 0.19140317564869455,
            "optical_throughput_coefficient_std": 0.00835591540715762,
            "method": "Muon Rings",
            "validity_start": datetime(2024, 9, 24, 15, 6, 25, 976202),
            "validity_end": datetime(2024, 9, 24, 15, 6, 38, 1943),
            "obs_id": 101,
            "tel_id": 1,
            "n_events": 3,
        }

        assert containers[1].optical_throughput_coefficient == pytest.approx(
            expected_values["optical_throughput_coefficient"], rel=1e-6
        )
        assert containers[1].optical_throughput_coefficient_std == pytest.approx(
            expected_values["optical_throughput_coefficient_std"], rel=1e-6
        )

        assert containers[1].method == expected_values["method"]
        assert containers[1].validity_start == expected_values["validity_start"]
        assert containers[1].validity_end == expected_values["validity_end"]
        assert containers[1].obs_id == expected_values["obs_id"]
        assert containers[1].tel_id == expected_values["tel_id"]
        assert containers[1].n_events == expected_values["n_events"]

    @pytest.mark.muon()
    @pytest.mark.db()
    def test_upload_muon_data_db(self):
        self.data["CalculateThroughputWithMuons"][
            "input_url"
        ] = self.input_good_muon_table_lst
        test_calculate_throughput_muon_tool = CalculateThroughputWithMuons(
            config=Config(self.data)
        )
        test_calculate_throughput_muon_tool.setup()

        test_calculate_throughput_muon_tool.throughput_containers[
            1
        ] = OpticalThoughtputContainer(
            optical_throughput_coefficient=1,
            optical_throughput_coefficient_std=0.1,
            method="Muon Rings",
            validity_start=datetime(1970, 1, 1, 17, 49, 37, 629896),
            validity_end=datetime(1970, 1, 1, 17, 49, 37, 630035),
            obs_id=101,
            tel_id=1,
            n_events=1,
        )
        test_calculate_throughput_muon_tool.finish()

        with CalibPipeDatabase(
            **self.data["database_configuration"],
        ) as connection:
            qtable = TableHandler.read_table_from_database(
                type(OpticalThoughtputContainer()), connection
            )

            assert qtable is not None
            uploaded_container = (
                test_calculate_throughput_muon_tool.throughput_containers[1]
            )
            assert qtable[-1]["tel_id"] == uploaded_container["tel_id"]
            assert qtable[-1]["obs_id"] == uploaded_container["obs_id"]
            assert qtable[-1]["method"] == uploaded_container["method"]
            assert (
                qtable[-1]["optical_throughput_coefficient"]
                == uploaded_container["optical_throughput_coefficient"]
            )
            assert (
                qtable[-1]["optical_throughput_coefficient_std"]
                == uploaded_container["optical_throughput_coefficient_std"]
            )
            assert qtable[-1]["n_events"] == uploaded_container["n_events"]
            assert qtable[-1]["validity_start"].tzinfo is not None
            assert qtable[-1]["validity_end"].tzinfo is not None

    @pytest.mark.muon()
    @pytest.mark.db()
    def test_muon_table(self):
        self.data["CalculateThroughputWithMuons"][
            "input_url"
        ] = self.input_good_muon_table_lst
        test_calculate_throughput_muon_tool = CalculateThroughputWithMuons(
            config=Config(self.data)
        )
        test_calculate_throughput_muon_tool.setup()
        test_calculate_throughput_muon_tool.throughput_containers[
            1
        ] = OpticalThoughtputContainer(
            optical_throughput_coefficient=1,
            optical_throughput_coefficient_std=0.1,
            method="Muon Rings",
            validity_start=datetime(1970, 1, 1, 17, 49, 37, 629896),
            validity_end=datetime(1970, 1, 1, 17, 49, 37, 630035),
            obs_id=101,
            tel_id=1,
            n_events=1,
        )
        test_calculate_throughput_muon_tool.finish()
        table_path = test_calculate_throughput_muon_tool.output_url
        written_table = QTable.read(table_path, format="ascii.ecsv")

        assert isinstance(
            written_table["validity_start"][0], Time
        ), "validity_start should be an Astropy Time object."
        assert isinstance(
            written_table["validity_end"][0], Time
        ), "validity_end should be an Astropy Time object."
        assert (
            written_table["validity_start"][0].scale == "utc"
        ), "validity_start should be timezone aware."
        assert (
            written_table["validity_end"][0].scale == "utc"
        ), "validity_end should be timezone aware."
        assert written_table["obs_id"][0] == 101
        assert written_table["tel_id"][0] == 1
        assert written_table["method"][0] == "Muon Rings"
        assert written_table["optical_throughput_coefficient"][0] == 1
        assert written_table["optical_throughput_coefficient_std"][0] == 0.1
        assert written_table["n_events"][0] == 1
