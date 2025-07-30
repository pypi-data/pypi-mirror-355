import os
import unittest

import polars as pl
from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.simulator import PowerSeriesSimulator

from midas_commercials.module import CommercialDataModule


class TestCommercialDataSimulator(unittest.TestCase):
    def setUp(self):
        data_path = RuntimeConfig().paths["data_path"]
        tmp_path = os.path.abspath(os.path.join(data_path, "tmp"))
        os.makedirs(tmp_path, exist_ok=True)

        CommercialDataModule().download(data_path, tmp_path, False)

        self.data_path = RuntimeConfig().paths["data_path"]
        self.file_path = RuntimeConfig().data["commercials"]["name"]
        self.start_date = "2021-11-16 16:00:00+0100"

    def test_init(self):
        sim = PowerSeriesSimulator()
        sim.init(
            "TestSimulator-0",
            start_date=self.start_date,
            data_path=self.data_path,
            filename=self.file_path,
        )

        self.assertIsInstance(sim.data, pl.LazyFrame)
        # self.assertFalse(sim.load_q) 

    def test_create(self):
        sim = PowerSeriesSimulator()
        sim.init(
            "TestSimulator-0",
            start_date=self.start_date,
            data_path=self.data_path,
            filename=self.file_path,
        )

        sim.create(1, "CalculatedQTimeSeries", name="SmallHotel")

        self.assertEqual(1, len(sim.models))

        sim.create(2, "CalculatedQTimeSeries", name="SuperMarket")

        self.assertEqual(3, len(sim.models))

    def test_step_and_get_data(self):
        sim = PowerSeriesSimulator()
        sim.init(
            "TestSimulator-0",
            start_date=self.start_date,
            data_path=self.data_path,
            filename=self.file_path,
            data_step_size=3600,
        )

        qsr_ent = sim.create(
            1, "CalculatedQTimeSeries", name="QuickServiceRestaurant"
        )
        sm_ent = sim.create(2, "CalculatedQTimeSeries", name="SmallOffice")

        sim.step(0, dict())

        data = sim.get_data(
            {
                qsr_ent[0]["eid"]: ["p_mw", "q_mvar"],
                sm_ent[0]["eid"]: ["p_mw", "q_mvar"],
                sm_ent[1]["eid"]: ["p_mw", "q_mvar"],
            }
        )

        self.assertAlmostEqual(0.0229005, data[qsr_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0110912, data[qsr_ent[0]["eid"]]["q_mvar"])
        self.assertAlmostEqual(0.0142743, data[sm_ent[0]["eid"]]["p_mw"])
        self.assertAlmostEqual(0.0069134, data[sm_ent[0]["eid"]]["q_mvar"])
        self.assertAlmostEqual(
            data[sm_ent[0]["eid"]]["p_mw"], data[sm_ent[1]["eid"]]["p_mw"]
        )
        self.assertAlmostEqual(
            data[sm_ent[0]["eid"]]["q_mvar"], data[sm_ent[1]["eid"]]["q_mvar"]
        )


if __name__ == "__main__":
    unittest.main()
