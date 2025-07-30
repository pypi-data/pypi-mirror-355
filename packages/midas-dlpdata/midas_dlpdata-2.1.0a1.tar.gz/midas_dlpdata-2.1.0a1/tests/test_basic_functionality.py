import os
import shutil
import unittest

from midas.api.fnc_run import run as midas_run
from midas.util.runtime_config import RuntimeConfig

from midas_dlp.module import DLPDataModule


class TestBasicFunctionality(unittest.TestCase):
    def setUp(self):
        self.filedir = os.path.abspath(os.path.join(__file__, ".."))
        # RuntimeConfig().load(
        #     {
        #         "paths": {
        #             "output_path": self.filedir,
        #             "scenario_path": self.filedir,
        #             "data_path": self.filedir,
        #         }
        #     }
        # )
        self.scenario_file = os.path.join(self.filedir, "dlp_test.yml")
        # self.results_db = os.path.join(self.filedir, "dlp_test_results.hdf5")
        # mod = DLPDataModule()
        # mod.download(
        #     self.filedir, os.path.join(self.filedir, "tmp"), False, False
        # )

        data_path = RuntimeConfig().paths["data_path"]
        tmp_path = os.path.abspath(os.path.join(data_path, "tmp"))
        os.makedirs(tmp_path, exist_ok=True)
        print(data_path, tmp_path)
        DLPDataModule().download(data_path, tmp_path, False)
        print(os.listdir(data_path))

    def test_run_scenario(self):
        midas_run(
            "dlp_test_example",
            {},
            self.scenario_file,
            skip_configure=True,
            skip_download=True,
        )
        # TODO test analyze


if __name__ == "__main__":
    unittest.main()
