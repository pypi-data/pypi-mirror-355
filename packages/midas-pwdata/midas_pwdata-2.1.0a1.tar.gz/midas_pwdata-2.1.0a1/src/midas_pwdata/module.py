"""MIDAS upgrade module for PV and Wind timeseries data simulator."""

import logging
import os
import platform

import click
import pandas as pd
import wget
from midas.util.dict_util import set_default_int
from midas.util.runtime_config import RuntimeConfig
from midas_powerseries.module import PowerSeriesModule

# from .download import download_gen

LOG = logging.getLogger(__name__)

if platform.system() == "Windows" or platform.system() == "Darwin":
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context


class PVWindDataModule(PowerSeriesModule):
    def __init__(self):
        super().__init__(
            module_name="pwdata",
            default_scope_name="midasmv",
            default_sim_config_name="PVWindData",
            log=LOG,
        )

        self._filename = "pvwind_profiles.csv"

    def check_sim_params(self, module_params):
        super().check_sim_params(module_params)
        self.sim_params.setdefault("filename", self._filename)
        self.sim_params["is_load"] = False
        self.sim_params["is_sgen"] = True
        set_default_int(self.sim_params, "data_step_size", 3600)

    def _download_and_read(self, config, tmp_path, plant):
        data = pd.DataFrame()
        base_url = (
            config["base_url"] + config[f"{plant}_url"] + config["postfix"]
        )
        if plant == "pv":
            usecols = [0, 1, 3]
        elif plant == "wind":
            usecols = [0, 1, 4, 5]
        years = list(
            range(int(config["first_year"]), int(config["last_year"]) + 1)
        )
        # years = [2015]
        for year in years:
            index = pd.date_range(
                start=f"{year}-01-01 00:00:00",
                end=f"{year}-12-31 23:45:00",
                freq="900s",
            )
            url = base_url + f"{year}.csv"

            LOG.debug("Downloading '%s'...", url)
            fname = wget.download(url, out=tmp_path)
            click.echo()
            LOG.debug("Download complete")

            try:
                ydata = pd.read_csv(
                    fname,
                    sep=";",
                    skip_blank_lines=True,
                    skiprows=3,
                    encoding="utf-16-le",
                    # parse_dates=[[0, 1]],
                    dayfirst=True,
                    decimal=",",
                    usecols=usecols,
                )
            except Exception:
                LOG.debug(
                    "Decoding file with 'utf-16-le' failed. "
                    "Now trying 'utf-16-be'."
                )
                ydata = pd.read_csv(
                    fname,
                    sep=";",
                    skip_blank_lines=True,
                    skiprows=3,
                    encoding="utf-16-be",
                    # parse_dates=[[0, 1]],
                    dayfirst=True,
                    decimal=",",
                    usecols=usecols,
                )
            if "von" in ydata.columns:
                von = "von"
            elif "Von" in ydata.columns:
                von = "Von"
            else:
                raise ValueError(
                    "Dateformat has changed and does not work anymore."
                )

            ydata["Datum_Von"] = pd.to_datetime(
                ydata.Datum.astype(str) + " " + ydata[von].astype(str),
                format="%d.%m.%Y %H:%M",
            )
            ydata = ydata.drop(["Datum", von], axis=1).set_index("Datum_Von")
            von = "Datum_Von"

            try:
                ydata.index = ydata.index.tz_localize(
                    "Europe/Berlin", ambiguous="infer"
                )
            except Exception as exc:
                LOG.debug(
                    "Got exception '%s' while localizing dataset."
                    "Will try a different strategy.",
                    exc,
                )
                ydata.index = ydata.index.tz_localize(
                    "Europe/Berlin", ambiguous=True
                )

            ydata.index = (
                ydata.index.tz_convert("UTC") + pd.Timedelta("1 hour")
            ).tz_localize(None)
            data = pd.concat([data, ydata.reindex(index, method="nearest")])

        if von in data.columns:
            data = data.drop(von, axis=1)
        return data

    def download(self, data_path, tmp_path, force):
        """
        Download and convert timeseries from 50hertz.

        Those are generator timeseries for PV and windpower.

        """

        LOG.info("Preparing generator timeseries...")
        config = RuntimeConfig().data["generator_timeseries"][0]

        output_path = os.path.abspath(
            os.path.join(data_path, self._filename)
        )  # config["name"]))
        if output_path.endswith(".hdf5"):
            output_path = f"{output_path[:-4]}csv"

        if os.path.exists(output_path):
            LOG.debug("Found existing dataset at '%s'.", output_path)
            if not force:
                return

        pv_data = self._download_and_read(config, tmp_path, "pv")
        wind_data = self._download_and_read(config, tmp_path, "wind")
        data = pd.concat([pv_data, wind_data], axis=1)
        data.columns = ["solar_p_mw", "onshore_p_mw", "offshore_p_mw"]

        data = data / data.max()

        data.to_csv(output_path, index_label="timestamp")
        LOG.info("Successfully created database for solar and wind power.")

    def analyze(
        self,
        name: str,
        data: pd.HDFStore,
        output_folder: str,
        start: int,
        end: int,
        step_size: int,
        full: bool,
    ):
        # No analysis, yet
        pass
