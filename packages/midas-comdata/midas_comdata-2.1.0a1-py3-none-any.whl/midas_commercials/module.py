import logging
import os
import platform
import shutil
import subprocess
import tarfile

import pandas as pd
import wget
from midas.util.dict_util import set_default_int
from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.module import PowerSeriesModule

LOG = logging.getLogger(__name__)

if platform.system() == "Windows" or platform.system() == "Darwin":
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context


class CommercialDataModule(PowerSeriesModule):
    def __init__(self):
        super().__init__(
            module_name="comdata",
            default_scope_name="midasmv",
            default_sim_config_name="CommercialData",
            # default_import_str="midas_powerseries"
            log=LOG,
        )

        self._filename = "commercial_profiles.csv"

    # def check_module_params(self, m_p):
    #     super().check_module_params(m_p)
    #     m_p["data_scaling"] = 0.001

    def check_sim_params(self, m_p):
        super().check_sim_params(m_p)
        self.sim_params.setdefault("filename", self._filename)
        set_default_int(self.sim_params, "data_step_size", 3600)

    def download(
        self, data_path: str, tmp_path: str, force: bool
    ):
        """Download and convert the commercial dataset.

        The datasets are downloaded from
        https://openei.org/datasets/files/961/pub

        """
        LOG.info("Preparing commercial datasets...")

        # We allow multiple datasets here (although not tested, yet)
        # for config in RuntimeConfig().data["commercials"]:
        config = RuntimeConfig().data["commercials"]
        output_path = os.path.abspath(os.path.join(data_path, self._filename))

        if os.path.exists(output_path):
            LOG.debug("Found existing dataset at %s.", output_path)
            if not force:
                return

        # Construct the final download locations
        loc_url = config["base_url"] + config["loc_url"]
        files = [
            (loc_url + f + config["post_fix"]).rsplit("/", 1)[1]
            for f, _ in config["data_urls"]
        ]
        for idx in range(len(files)):
            file_path = os.path.join(tmp_path, files[idx])
            if not os.path.exists(file_path) or force:
                if os.path.exists(file_path):
                    os.remove(file_path)
                LOG.debug("Downloading '%s'...", files[idx])
                files[idx] = wget.download(
                    loc_url + config["data_urls"][idx][0] + config["post_fix"],
                    out=tmp_path,
                )
                # click.echo()
            else:
                files[idx] = file_path
        LOG.debug("Download complete.")

        # Converting data
        date_range = pd.date_range(
            start="2004-01-01 00:00:00",
            end="2004-12-31 23:00:00",
            freq="h",
            tz="Europe/Berlin",
        )
        # Since 2004 is a leap year, we need to add an additional
        # day.
        dr_pt1 = pd.date_range(
            start="2004-01-01 00:00:00",
            end="2004-02-28 23:00:00",
            freq="h",
            tz="Europe/Berlin",
        )
        LOG.debug("Converting files...")
        # Now assemble the distinct files to one dataframe
        data = pd.DataFrame(index=date_range)
        for (src, tar), file_ in zip(config["data_urls"], files):
            fpath = os.path.join(tmp_path, file_)
            tsdat = pd.read_csv(fpath, sep=",")
            tsdat1 = tsdat.iloc[: len(dr_pt1)]
            tsdat1 = pd.concat([tsdat1, tsdat1.iloc[-24:]])
            tsdat2 = tsdat.iloc[len(dr_pt1) :]
            tsdat = pd.concat([tsdat1, tsdat2])
            tsdat.index = date_range
            data[tar] = tsdat[config["el_cols"]].sum(axis=1) * 1e-3
        LOG.debug("Conversion complete.")

        # Create hdf5 database
        # data.to_hdf(output_path, "load_pmw", "w")
        # data = data.reset_index()
        data.to_csv(output_path, index=False)
        LOG.info("Successfully created database for commercial dataset.")
