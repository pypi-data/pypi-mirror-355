"""This module contains the model for data simulators."""

import logging
import math
from datetime import datetime
from typing import cast

import numpy as np
import polars as pl
from midas.util.compute_q import compute_p, compute_q

LOG = logging.getLogger(__name__)


class DataModel:
    """A model for a single load or sgen time series.

    This model can be used to "simulate" a time series of active and,
    if provided, reactive power values. The model is designed to
    simulate one year but the time resolution of the data needs to be
    specified. This time resolution can be different than the step size
    for one step but if the step size is lower, values will be returned
    repeatedly.

    If that behavior is not desired, the linear interpolation function
    of the model can be used. This can also be combined with the
    randomization function. Those can be activated by passing the
    corresponding flags (see Parameter section).

    If the data does not contain a reactive power time series, the
    model will calculate reactive power based on the cos phi, which
    should be provided before each step. There is an option to
    randomize the output of the cos phi calculation as well.

    The main input for the model is a datetime object for the time to
    be simulated. Month, day, hour, minute, and second will be used to
    determine the corresponding value of the data set. Year information
    will be dropped.

    This has two consequences. First, the model can be used to simulate
    several years and, secondly, the data set needs to be exactly for
    one year. Larger data sets will be "cropped" to one year and
    smaller data sets will probably lead to an error.

    Parameters
    ----------
    data_p : pandas.DataFrame
        Contains values (either load or sgen) for active power. The
        index columns are simple *int*.
    data_q : pandas.DataFrame
        Contains values (either load or sgen) for reactive power. The
        index columns are simple *int*. If *None* is provided for
        *data_q*, the cos phi is used in each step to calculate a value
        for *q*.
    data_step_size: int
        Timely resolution of the data in seconds.
    seed : int, optional
        A seed for the random number generator.
    interpolate : bool, optional
        If set to *True*, interpolation is applied when values between
        full 15-minute intervalls are requested.
    randomize_data : bool, optional
        If set to *True*, a normally distributed random noise is
        applied to all outputs.
    randomize_cos_phi : bool, optional
        If set to *True* and data_q is not provided, the cos phi for
        the calculation of *q* is randomized.
    date_index : bool, optional
        Set this to *True* if the data has datetime as index instead of
        ints (planned but not yet supported).
    noise_factor: float, optional
        Set this to increase or lower the noise if randomization is
        activated.

    Attributes
    ----------
    now_dt : datetime.datetime
        *now_dt is an input and needs to be provided in each step.*
        The current simulated time. Is used to calculate the index for
        the current value in the time series.
    cos_phi : float
        *cos_phi is an input and needs to be provided in each step.*
        The phase angle is used to calculate reactive power if no reactive
        power time series is provided.
    p_mw : float
        *p_mw is an output.* The active power for the current step.
    q_mvar : float
        *q_mvar is an output.* The reactive power for the current step.

    """

    def __init__(self, data: pl.LazyFrame, data_step_size: int, **params):
        self.data = data.collect()
        self.sps = data_step_size
        self.p_calculated = params["p_calculated"]
        self.q_calculated = params["q_calculated"]
        if self.p_calculated and self.q_calculated:
            LOG.warning(
                "Both p_calculated and q_calculated are set to True, which is"
                " not supported. Setting p_calculated to False"
            )
            self.p_calculated = False
        self.calculate_missing = params.get("calculate_missing", False)
        self.date_index = params.get("date_index", False)
        self._cols = self.data.collect_schema().names()

        # RNG
        self.seed = params.get("seed", None)
        self.rng = np.random.RandomState(self.seed)

        self.interpolate = params.get("interpolate", False)
        self.randomize_data = params.get("randomize_data", False)
        self.randomize_cos_phi = params.get("randomize_cos_phi", False)
        self.noise_factor = params.get("noise_factor", 0.2)

        # Statistics
        if "p" in self._cols:
            self.p_std = self.data.select(pl.std("p")).item()

            # FIXME: handle data that is longer/shorter than a year
            self.p_mwh_per_a = (
                self.data.select(pl.std("p")).item() / self.sps * 3_600
            )
        else:
            self.p_std = None
            self.p_mwh_per_a = 0
        if "q" in self._cols:
            self.q_std = self.data.select(pl.std("q")).item()
        else:
            self.q_std = None

        # Inputs
        self.now_dt: datetime | None = None
        self.cos_phi: float = 0.0

        # Outputs
        self.p_mw: float | None = None
        self.q_mvar: float | None = None
        self.p_set_mw: float | None = None
        self.q_set_mvar: float | None = None

    def step(self):
        """Perform a simulation step."""

        self.p_mw = None
        self.q_mvar = None

        self._interpolation()
        self._randomization()

        self._random_cos_phi()

        if self.p_calculated:
            self.p_mw = compute_p(cast(float, self.q_mvar), self.cos_phi)

        if self.q_calculated:
            self.q_mvar = compute_q(cast(float, self.p_mw), self.cos_phi)

        if self.p_set_mw is not None and "p" in self._cols:
            self.p_mw = self.p_set_mw
            self.p_set_mw = None

        if self.q_set_mvar is not None and "q" in self._cols:
            self.q_mvar = self.q_set_mvar
            self.q_set_mvar = None

        if self.p_mw is not None and self.q_mvar is not None:
            self.cos_phi = calculate_cos_phi(self.p_mw, self.q_mvar)
        else:
            self.cos_phi = 0

    def _interpolation(self):
        # We assume that the dataset starts on the first of the year.
        assert self.now_dt is not None
        dif = self.now_dt - self.now_dt.replace(
            month=1, day=1, hour=0, minute=0, second=0
        )
        dif_s = dif.total_seconds()

        tidx = int(dif_s // self.sps) % self.data.select(pl.len()).item()
        tidx_end = (tidx + 1) % self.data.select(pl.len()).item()
        current_second = (
            self.now_dt.minute * 60 + self.now_dt.second
        ) % self.sps
        x_vals = np.array([0, self.sps])

        # Apply interpolation
        if "p" in self._cols and not self.p_calculated:
            if self.interpolate:
                self.p_mw = cast(
                    float,
                    np.interp(
                        current_second,
                        x_vals,
                        [
                            self.data.select(pl.col("p")).row(tidx)[0],
                            self.data.select(pl.col("p")).row(tidx_end)[0],
                        ],
                    ),
                )
            else:
                self.p_mw = self.data.select(pl.col("p")).row(tidx)[0]
        if "q" in self._cols and not self.q_calculated:
            if self.interpolate:
                self.q_mvar = cast(
                    float,
                    np.interp(
                        current_second,
                        x_vals,
                        [
                            self.data.select(pl.col("q")).row(tidx)[0],
                            self.data.select(pl.col("q")).row(tidx_end)[0],
                        ],
                    ),
                )
            else:
                self.q_mvar = self.data.select(pl.col("q")).row(tidx)[0]

    def _randomization(self):
        if self.randomize_data:
            if "p" in self._cols and not self.p_calculated:
                noise = self.rng.normal(
                    scale=(self.p_std * self.noise_factor), loc=0.0
                )
                self.p_mw = max(0, self.p_mw + noise)

            if "q" in self._cols and not self.q_calculated:
                noise = self.rng.normal(
                    scale=(self.q_std * self.noise_factor), loc=0.0
                )
                self.q_mvar = max(0, self.q_mvar + noise)
                # FIXME what about negative numbers?

    def _random_cos_phi(self):
        if (self.p_calculated or self.q_calculated) and self.randomize_cos_phi:
            self.cos_phi = max(
                0, min(1.0, self.rng.normal(scale=0.02, loc=0.9))
            )


@staticmethod
def calculate_cos_phi(p, q) -> float:
    tmp = p**2 + q**2
    if tmp != 0:
        cos_phi = p / math.sqrt(tmp)
    else:
        cos_phi = 0.0

    return cos_phi
