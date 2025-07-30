"""
This module contains the test cases for the simbench data simulator.

"""

import os
import unittest

from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.model import DataModel
from midas_powerseries.simulator import PowerSeriesSimulator

from midas_pwdata.module import PVWindDataModule


class TestSimulator(unittest.TestCase):
    """Test case for the simbench data simulator."""

    def setUp(self):
        data_path = RuntimeConfig().paths["data_path"]
        tmp_path = os.path.abspath(os.path.join(data_path, "tmp"))
        os.makedirs(tmp_path, exist_ok=True)

        mod = PVWindDataModule()
        mod.download(data_path, tmp_path, False)

        self.sim = PowerSeriesSimulator()
        self.sim_params = {
            "sid": "TestSimulator-0",
            "step_size": 900,
            "start_date": "2019-11-16 15:45:00+0100",
            "data_path": RuntimeConfig().paths["data_path"],
            "filename": mod._filename,
        }

    def test_init(self):
        sim = self.sim
        meta = sim.init(**self.sim_params)

        self.assertIsInstance(meta, dict)

    def test_create(self):
        sim = self.sim
        sim.init(**self.sim_params)

        # Test create
        entities = sim.create(3, "CalculatedQTimeSeries", name="solar_p_mw")
        self.assertEqual(len(entities), 3)
        for entity in entities:
            self.assertIsInstance(entity, dict)
            self.assertIn(entity["eid"], sim.models)
            self.assertIsInstance(sim.models[entity["eid"]], DataModel)

        self.assertEqual("CalculatedQTimeSeries-0", entities[0]["eid"])

        entities = sim.create(2, "CalculatedQTimeSeries", name="onshore_p_mw")
        self.assertEqual(len(entities), 2)
        for entity in entities:
            self.assertIsInstance(entity, dict)
            self.assertIn(entity["eid"], sim.models)
            self.assertIsInstance(sim.models[entity["eid"]], DataModel)

        self.assertEqual("CalculatedQTimeSeries-4", entities[1]["eid"])

        entities = sim.create(1, "CalculatedQTimeSeries", name="solar_p_mw")
        self.assertEqual(len(entities), 1)
        self.assertEqual("CalculatedQTimeSeries-5", entities[0]["eid"])

    def test_step_and_get_data(self):
        sim = self.sim
        sim.init(**self.sim_params)

        pv_ent = sim.create(2, "CalculatedQTimeSeries", name="solar_p_mw")
        wind_ent = sim.create(1, "CalculatedQTimeSeries", name="onshore_p_mw")
        wind_off_ent = sim.create(
            1, "CalculatedQTimeSeries", name="offshore_p_mw"
        )
        sim.step(0, dict())

        data = sim.get_data(
            {
                pv_ent[0]["eid"]: ["p_mw", "q_mvar"],
                pv_ent[1]["eid"]: ["p_mw", "q_mvar"],
                wind_ent[0]["eid"]: ["p_mw", "q_mvar"],
                wind_off_ent[0]["eid"]: ["p_mw", "q_mvar"],
            }
        )

        self.assertAlmostEqual(0.0943021, data[pv_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.42635096, data[wind_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(
            0.74847098, data[wind_off_ent[0]["eid"]]["p_mw"]
        )

    def test_get_data_info(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)
        sim.create(1, "CalculatedQTimeSeries", name="solar_p_mw", scaling=1)
        sim.create(1, "CalculatedQTimeSeries", name="solar_p_mw", scaling=2)
        sim.create(5, "CalculatedQTimeSeries", name="onshore_p_mw")
        info = sim.get_data_info()

        self.assertIn("CalculatedQTimeSeries-0", info)
        self.assertIn("CalculatedQTimeSeries-1", info)
        self.assertEqual(
            info["CalculatedQTimeSeries-0"]["p_mwh_per_a"] * 2,
            info["CalculatedQTimeSeries-1"]["p_mwh_per_a"],
        )
        self.assertEqual(2, info["num"]["solar_p_mw"])
        self.assertEqual(5, info["num"]["onshore_p_mw"])
        self.assertNotIn("offshore_p_mw", info["num"])
        # self.assertEqual(7, info["num_sgens"])


if __name__ == "__main__":
    unittest.main()
