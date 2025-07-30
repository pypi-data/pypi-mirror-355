import os
import subprocess
import tarfile

import pandas as pd
from midas.scenario.upgrade_module import ModuleParams
from midas_powerseries.module import PowerSeriesModule

from . import LOG


class SmartNordDataModule(PowerSeriesModule):
    def __init__(self):
        super().__init__(
            module_name="sndata",
            default_scope_name="midasmv",
            default_sim_config_name="SmartNordData",
            log=LOG,
        )

        self._filename = "smart_nord_profiles.csv"

    def check_sim_params(self, mp: ModuleParams):
        super().check_sim_params(mp)
        self.sim_params.setdefault("filename", self._filename)

    def download(self, data_path: str, tmp_path: str, force: bool):
        """Download and convert the Smart Nord dataset.

        The dataset is stored inside of gitlab and will be downloaded from
        there and converted afterwards.

        """

        LOG.info("Preparing Smart Nord datasets...")
        token = "fDaPqqSuMBhsXD8nQ_Nn"  # read only Gitlab token for midas_data

        # # There is only one dataset
        # config = RuntimeConfig().data["smart_nord"][0]
        # if if_necessary and not config.get("load_on_start", False):
        #     return
        output_path = os.path.abspath(os.path.join(data_path, self._filename))
        if os.path.exists(output_path):
            LOG.debug("Found existing datasets at %s.", output_path)
            if not force:
                return

        zip_path = os.path.join(
            tmp_path, "smart_nord_data", "HouseholdProfiles.tar.gz"
        )
        if not os.path.exists(zip_path):
            LOG.debug("Downloading dataset...")
            try:
                subprocess.check_output(
                    [
                        "git",
                        "clone",
                        f"https://midas:{token}@gitlab.com/midas-mosaik/"
                        "midas-data.git",
                        os.path.join(tmp_path, "smart_nord_data"),
                    ]
                )
                LOG.debug("Download complete.")
            except Exception as err:
                print(
                    "Something went wrong. Please make sure git installed "
                    "and in your PATH environment variable."
                )
                LOG.error(
                    "Could not download Smart Nord Data: %s. This may be "
                    "caused by a missing git installation. Please make sure "
                    "git is installed and in your PATH environment variable.",
                    err,
                )

        LOG.debug("Extracting...")
        with tarfile.open(zip_path, "r:gz") as tar_ref:
            tar_ref.extractall(tmp_path)
        LOG.debug("Extraction complete.")

        tmp_name = os.path.join(tmp_path, "HouseholdProfiles.hdf5")
        tmp_data = pd.HDFStore(tmp_name)
        data = tmp_data["load_pmw"]
        tmp_data.close()
        lands = {}
        for i in range(8):
            land_cols = [c for c in data.columns if f"Load{i}" in c]
            lands[f"Land_{i}"] = data[land_cols].sum(axis=1)
        data.columns = [f"House_{i:03d}" for i, _ in enumerate(data.columns)]
        for land_id, land in lands.items():
            data[land_id] = land

        data.to_csv(output_path, index=False)
        LOG.info("Successfully created database for Smart Nord datasets.")
