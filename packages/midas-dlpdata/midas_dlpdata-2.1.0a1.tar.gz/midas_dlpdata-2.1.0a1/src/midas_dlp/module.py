import logging
import os
import platform
import shutil
import subprocess
import tarfile
from zipfile import ZipFile

import pandas as pd
import wget
from midas.util.dict_util import set_default_int
from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.module import PowerSeriesModule

LOG = logging.getLogger(__name__)

if platform.system() == "Windows" or platform.system() == "Darwin":
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context


class DLPDataModule(PowerSeriesModule):
    def __init__(self):
        super().__init__(
            module_name="dlpdata",
            default_scope_name="midasmv",
            default_sim_config_name="DefaultLoadProfiles",
            log=LOG,
        )

        self._filename = "bdew_default_load_profiles.csv"
        self._model = "midas_dlp.model:DLPModel"

    def check_sim_params(self, m_p):
        super().check_sim_params(m_p)
        self.sim_params.setdefault("filename", self._filename)
        self.sim_params.setdefault("model_import_str", self._model)
        self.sim_params["use_custom_time_series"] = True

    def download(
        self, data_path: str, tmp_path: str, force: bool
    ):
        """Download and convert default load profiles.

        The default load profiles can be downloaded from the BDEW (last
        visited on 2020-07-07):

        https://www.bdew.de/energie/standardlastprofile-strom/

        """

        LOG.info("Preparing default load profiles...")
        # Specify the paths, we only have one provider for those profiles.
        config = RuntimeConfig().data["default_load_profiles"]

        output_path = os.path.abspath(os.path.join(data_path, config["name"]))

        if os.path.exists(output_path):
            LOG.debug("Found existing dataset at %s.", output_path)
            if not force:
                return

        # Download the file
        fname = config["base_url"].rsplit("/", 1)[-1]
        tmp_file = os.path.join(tmp_path, fname)
        if not os.path.exists(tmp_file) or force:
            LOG.debug("Downloading '%s'...", config["base_url"])
            os.makedirs(tmp_path, exist_ok=True)
            fname = wget.download(config["base_url"], out=tmp_file)
            print()  # To get a new line after wget output
            LOG.debug("Download complete.")

        # Specify unzip target
        target = os.path.join(tmp_path, "dlp")
        if os.path.exists(target):
            LOG.debug("Removing existing files.")
            shutil.rmtree(target)

        # Extract the file

        LOG.debug("Extracting profiles...")
        with ZipFile(os.path.join(tmp_path, fname), "r") as zip_ref:
            zip_ref.extractall(os.path.join(tmp_path, target))
        LOG.debug("Extraction complete.")

        excel_path = os.path.join(target, config["filename"])

        # Load excel sheet
        data = pd.read_excel(
            io=excel_path,
            sheet_name=config["sheet_names"],
            header=[1, 2],
            skipfooter=1,
        )

        # Create a hdf5 datebase from the sheet
        LOG.debug("Creating hdf5 database...")
        res = {}
        for name in config["sheet_names"]:
            # grp = h5f.create_group(name)
            res[name] = [0] * 96
            for season in config["seasons"]:
                # subgrp = grp.create_group(season[1])
                for day in config["days"]:
                    # Bring last value to front
                    col_name = f"{name}_{season[1]}_{day[1]}"
                    res[col_name] = list(
                        data[name][(season[0], day[0])].values
                    )

        LOG.info("Successfully created database for default load profiles.")
        pd.DataFrame(res).to_csv(output_path, index=False)
        LOG.info("Successfully created database for commercial dataset.")
        print("Download complete")
