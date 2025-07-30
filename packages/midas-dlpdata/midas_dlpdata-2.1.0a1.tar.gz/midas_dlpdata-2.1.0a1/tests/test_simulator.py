import os
import shutil
import unittest

from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.simulator import PowerSeriesSimulator

from midas_dlp.model import DLPModel
from midas_dlp.module import DLPDataModule


class TestSimulator(unittest.TestCase):
    def setUp(self):
        # self.filedir = os.path.abspath(os.path.join(__file__, ".."))
        # RuntimeConfig().load(
        #     {
        #         "paths": {
        #             "output_path": self.filedir,
        #             "scenario_path": self.filedir,
        #             "data_path": self.filedir,
        #         }
        #     }
        # )
        data_path = RuntimeConfig().paths["data_path"]
        tmp_path = os.path.abspath(os.path.join(data_path, "tmp"))
        os.makedirs(tmp_path, exist_ok=True)

        DLPDataModule().download(data_path, tmp_path, False)

        self.sim_params = {
            "sid": "TestSimulator-0",
            "step_size": 900,
            "start_date": "2021-11-16 15:45:00+0100",
            "data_path": RuntimeConfig().paths["data_path"],
            "filename": "bdew_default_load_profiles.csv",
            "model_import_str": "midas_dlp.model:DLPModel",
        }
        self.profiles = [
            "G0",
            "G1",
            "G2",
            "G3",
            "G4",
            "G5",
            "G6",
            "H0",
            "L0",
            "L1",
            "L2",
        ]

    def test_create(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)

        for prof in self.profiles:
            sim.create(1, "CustomTimeSeries", name=prof, scaling=1.0)
        for eid, model in sim.models.items():
            self.assertIn("CustomTimeSeries", eid)
            self.assertIn(model.name, self.profiles)
            self.assertIsInstance(model, DLPModel)

    def test_step_and_get_data(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)

        outputs = {}
        for prof in self.profiles:
            entities = sim.create(
                1, "CustomTimeSeries", name=prof, scaling=1.0
            )
            outputs[entities[0]["eid"]] = ["p_mw", "q_mvar"]

        sim.step(0, {})
        data = sim.get_data(outputs)

        for idx, prof in enumerate(self.profiles):
            self.assertNotEqual(0.0, data[f"CustomTimeSeries-{idx}"]["p_mw"])
            self.assertNotEqual(0.0, data[f"CustomTimeSeries-{idx}"]["q_mvar"])

    def test_get_data_info(self):
        sim = PowerSeriesSimulator()
        sim.init(**self.sim_params)

        for prof in self.profiles:
            sim.create(1, "CustomTimeSeries", name=prof, scaling=1.0)

        info = sim.get_data_info()
        for idx, prof in enumerate(self.profiles):
            self.assertEqual(
                1.0, info[f"CustomTimeSeries-{idx}"]["p_mwh_per_a"]
            )
            self.assertEqual(1, info["num"][prof])

    # def tearDown(self):
    #     files_to_delete = [
    #         os.path.join(self.filedir, "bdew_default_load_profiles.csv"),
    #         os.path.join(self.filedir, "dlp_test_example_auto_script.py"),
    #         os.path.join(self.filedir, "dlp_test_example_cfg.yml"),
    #         os.path.join(self.filedir, "dlp_test_results.hdf5"),
    #     ]
    #     for f in files_to_delete:
    #         try:
    #             os.remove(f)
    #         except FileNotFoundError:
    #             pass
    #     try:
    #         shutil.rmtree(os.path.join(self.filedir, "tmp"))
    #     except FileNotFoundError:
    #         pass


if __name__ == "__main__":
    unittest.main()
