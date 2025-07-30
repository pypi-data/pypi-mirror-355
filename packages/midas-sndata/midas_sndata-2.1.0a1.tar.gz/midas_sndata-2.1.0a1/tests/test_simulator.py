"""
This module contains the test cases for the simbench data simulator.

"""

import os
import unittest

from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.model import DataModel
from midas_powerseries.simulator import PowerSeriesSimulator

import midas_smartnord
from midas_smartnord.module import SmartNordDataModule


class TestSimulator(unittest.TestCase):
    """Test case for the simbench data simulator."""

    def setUp(self):
        data_path = RuntimeConfig().paths["data_path"]
        tmp_path = os.path.abspath(os.path.join(data_path, "tmp"))
        os.makedirs(tmp_path, exist_ok=True)

        SmartNordDataModule().download(data_path, tmp_path, False)

        self.sim_params = {
            "sid": "TestSimulator-0",
            "step_size": 900,
            "start_date": "2021-11-16 15:45:00+0100",
            "data_path": data_path,
            "filename": SmartNordDataModule()._filename,
        }

    def test_init(self):
        sim = PowerSeriesSimulator()
        meta = sim.init(**self.sim_params)

        self.assertIsInstance(meta, dict)

    def test_create(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)

        # Test create
        entities = sim.create(3, "CalculatedQTimeSeries", name="Land_0")
        self.assertEqual(len(entities), 3)
        for entity in entities:
            self.assertIsInstance(entity, dict)
            self.assertIn(entity["eid"], sim.models)
            self.assertIsInstance(sim.models[entity["eid"]], DataModel)

        self.assertEqual("CalculatedQTimeSeries-0", entities[0]["eid"])

        entities = sim.create(1, "CalculatedQTimeSeries", name="Land_1")
        self.assertEqual(len(entities), 1)
        self.assertEqual("CalculatedQTimeSeries-3", entities[0]["eid"])

    def test_step_and_get_data(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)

        land_ent = sim.create(1, "CalculatedQTimeSeries", name="Land_0")
        land_ent.extend(sim.create(1, "CalculatedQTimeSeries", name="Land_1"))
        land_ent.extend(sim.create(1, "CalculatedQTimeSeries", name="Land_2"))
        house_ent = sim.create(1, "CalculatedQTimeSeries", name="House_000")
        house_ent.extend(
            sim.create(1, "CalculatedQTimeSeries", name="House_001")
        )

        sim.step(0, {})

        data = sim.get_data(
            {
                land_ent[0]["eid"]: ["p_mw", "q_mvar"],
                land_ent[1]["eid"]: ["p_mw", "q_mvar"],
                land_ent[2]["eid"]: ["p_mw", "q_mvar"],
                house_ent[0]["eid"]: ["p_mw", "q_mvar"],
                house_ent[1]["eid"]: ["p_mw", "q_mvar"],
            }
        )
        self.assertAlmostEqual(0.0170418, data[land_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0082537, data[land_ent[0]["eid"]]["q_mvar"])
        self.assertAlmostEqual(0.1163297, data[land_ent[1]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0563410, data[land_ent[1]["eid"]]["q_mvar"])
        self.assertAlmostEqual(0.0423342, data[land_ent[2]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0205034, data[land_ent[2]["eid"]]["q_mvar"])
        self.assertAlmostEqual(0.0001192, data[house_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0000577, data[house_ent[0]["eid"]]["q_mvar"])
        self.assertAlmostEqual(0.0000580, data[house_ent[1]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0000281, data[house_ent[1]["eid"]]["q_mvar"])

    def test_get_data_info(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)
        sim.create(1, "CalculatedQTimeSeries", name="Land_0", scaling=1)
        sim.create(1, "CalculatedQTimeSeries", name="Land_0", scaling=2)
        sim.create(5, "CalculatedQTimeSeries", name="House_000")
        info = sim.get_data_info()

        self.assertIn("CalculatedQTimeSeries-0", info)
        self.assertIn("CalculatedQTimeSeries-1", info)
        self.assertEqual(
            info["CalculatedQTimeSeries-0"]["p_mwh_per_a"] * 2,
            info["CalculatedQTimeSeries-1"]["p_mwh_per_a"],
        )
        # self.assertEqual(2, info["num_lands"])
        # self.assertEqual(5, info["num_households"])


if __name__ == "__main__":
    unittest.main()
