"""This module contains the default load profile data model."""

import numpy as np
import polars as pl
from midas.util.compute_q import compute_q
from midas.util.runtime_config import RuntimeConfig


class DLPModel:
    """A model to handle a default load profile."""

    def __init__(self, data, data_step_size, scaling, **params):
        data, self.name, mscaling = data
        self.data = {}
        for _, season in RuntimeConfig().data["default_load_profiles"][
            "seasons"
        ]:
            for _, day in RuntimeConfig().data["default_load_profiles"][
                "days"
            ]:
                key = f"{self.name}_{season}_{day}"
                self.data[key] = list(
                    list(data.select(pl.col(key)).collect())[0]
                )

        self.p_mwh_per_a = scaling

        self._rng = np.random.RandomState(params.get("seed", None))

        self._interpolate = params.get("interpolate", False)
        self._randomize_data = params.get("randomize_data", False)
        self._randomize_cos_phi = params.get("randomize_cos_phi", False)
        self._randomize_data_scale = params.get("randomize_data_scale", 0.05)
        self._randomize_cos_phi_scale = params.get(
            "randomize_cos_phi_scale", 0.01
        )

        # Inputs
        self.now_dt = None
        self.cos_phi = None

        # Outputs
        self.p_mw = None
        self.q_mvar = None

    def step(self):
        """Generate the data for the next time interval defined by
        now_dt.

        """
        if self.now_dt.month in {1, 2, 12}:
            season = "winter"
        elif self.now_dt.month in {6, 7, 8}:
            season = "summer"
        else:
            season = "transition"

        if self.now_dt.weekday() == 5:
            day = "saturday"
        elif self.now_dt.weekday() == 6:
            day = "sunday"
        else:
            day = "weekday"
        key = f"{self.name}_{season}_{day}"
        # +1 because now dt is in UTC and DLP start in UTC+1
        idx = int(self.now_dt.hour * 4 + self.now_dt.minute // 15)
        idx_interp = self.now_dt.hour * 4 + self.now_dt.minute / 15
        if self._interpolate and idx != idx_interp:
            cur_sec = (self.now_dt.minute * 60) % 900 + self.now_dt.second
            f_p = self.data[key][idx : idx + 2]
            if len(f_p) == 1:
                f_p = np.array([f_p[0], self.data[key][0]])
            self.p_mw = np.interp(cur_sec, [0, 900], f_p)
        else:
            self.p_mw = self.data[key][idx]

        if self._randomize_data:
            self.p_mw *= self._rng.normal(
                scale=self._randomize_data_scale, loc=1.0
            )
            self.p_mw = max(0, self.p_mw)

        if self._randomize_cos_phi:
            self.cos_phi = max(
                0,
                min(
                    2 * np.pi,
                    self._rng.normal(
                        scale=self._randomize_cos_phi_scale, loc=0.9
                    ),
                ),
            )

        self.p_mw *= self.p_mwh_per_a * 1e-6
        self.q_mvar = compute_q(self.p_mw, self.cos_phi)
