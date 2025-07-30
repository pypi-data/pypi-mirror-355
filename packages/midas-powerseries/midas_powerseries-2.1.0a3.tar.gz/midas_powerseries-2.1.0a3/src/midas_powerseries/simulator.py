"""This module contains a simulator for converted Smart Nord data.

The models itself are simple data provider.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Type, cast

import mosaik_api_v3
import numpy as np
import polars as pl
from midas.util.compute_q import compute_p, compute_q
from midas.util.dateformat import GER
from midas.util.dict_util import bool_from_dict, strtobool
from midas.util.logging import set_and_init_logger
from midas.util.runtime_config import RuntimeConfig
from mosaik_api_v3.types import Meta, SimId
from typing_extensions import override

from .meta import META
from .model import DataModel

LOG = logging.getLogger("midas_powerseries.simulator")


class PowerSeriesSimulator(mosaik_api_v3.Simulator):
    """A simulator for electrical power time series."""

    def __init__(self):
        super().__init__(META)

        self.sid: str = ""
        self.step_size: int = 0
        self.now_dt: datetime = datetime(1977, 1, 1)
        self.sim_time = 0
        self.seed: int | None = None
        self.rng: np.random.Generator = np.random.default_rng()
        self.interpolate = False
        self.randomize_data = False
        self.randomize_cos_phi = False
        self.cos_phi = 0.9

        self.data: pl.LazyFrame
        self.data_step_size = 0
        self.num_models = {}
        self.data_column_usage = {}
        self.models = {}
        self._create_data_model: Type[DataModel] = DataModel

    @override
    def init(
        self, sid: SimId, time_resolution: float = 1.0, **sim_params
    ) -> Meta:
        """Called exactly ones after the simulator has been started.

        :return: the meta dict (set by mosaik_api.Simulator)
        """
        # super().init(sid, **sim_params)
        self.sid = sid
        self.step_size = int(sim_params.get("step_size", 900))
        self.now_dt = datetime.strptime(
            sim_params["start_date"], GER
        ).astimezone(timezone.utc)

        self.has_datetime_index = bool_from_dict(
            sim_params, "has_datetime_index"
        )

        # Load the data
        data_path = sim_params.get(
            "data_path", RuntimeConfig().paths["data_path"]
        )
        file_path = os.path.join(data_path, sim_params["filename"])
        LOG.debug("Using db file at %s.", file_path)
        self.data_step_size = int(sim_params.get("data_step_size", 900))

        if file_path.endswith(".csv"):
            self.data = pl.scan_csv(file_path)
        else:
            raise NotImplementedError("Only csv is supported, yet. Sorry!")

        self.interpolate = bool_from_dict(sim_params, "interpolate")
        self.randomize_data = bool_from_dict(sim_params, "randomize_data")
        self.randomize_cos_phi = bool_from_dict(
            sim_params, "randomize_cos_phi"
        )

        self.cos_phi = sim_params.get("cos_phi", 0.9)

        # RNG
        self.seed = sim_params.get("seed", None)
        self.seed_max = 2**32 - 1
        if self.seed is not None:
            self.rng = np.random.default_rng(self.seed)
        else:
            LOG.debug("No seed provided. Using random seed.")

        model_fnc = sim_params.get("model_import_str", None)
        if model_fnc is not None:
            if ":" in model_fnc:
                mod, clazz = model_fnc.split(":")
            else:
                mod, clazz = model_fnc.rsplit(".", 1)
            mod = import_module(mod)
            self._create_data_model = getattr(mod, clazz)

        return self.meta

    def create(self, num, model, **model_params):
        """Initialize the simulation model instance (entity)

        :return: a list with information on the created entity

        """
        entities = []

        scaling = model_params.get("scaling", 1.0)
        for _ in range(num):
            # p_series = q_series = None
            p_calculated = q_calculated = calculate_missing = False
            name = model_params["name"]
            if isinstance(name, str):
                names = [name]
            else:
                names = name

            if len(names) > 2:
                msg = f"Too many column entries for mapping: {name}"
                raise ValueError(msg)

            for n in names:
                self.data_column_usage.setdefault(n, 0)
                self.data_column_usage[n] += 1

            if len(names) == 1:
                if model == "CalculatedPTimeSeries":
                    data = self.data.select(
                        compute_p(pl.col(name) * scaling).alias("p"),
                        (pl.col(name) * scaling).alias("q"),
                    )
                    calculate_missing = True
                    p_calculated = True
                if model == "ActiveTimeSeries":
                    data = self.data.select(
                        (pl.col(name) * scaling).alias("p")
                    )
                if model == "ReactiveTimeSeries":
                    data = self.data.select(
                        (pl.col(name) * scaling).alias("q")
                    )
                if model == "CustomTimeSeries":
                    data = self.data, name, scaling
                else:
                    model = "CalculatedQTimeSeries"
                    data = self.data.select(
                        (pl.col(name) * scaling).alias("p"),
                        compute_q(pl.col(name) * scaling).alias("q"),
                    )
                    calculate_missing = True
                    q_calculated = True
            else:
                model = "CombinedTimeSeries"
                data = self.data.select(
                    (pl.col(name[0]) * scaling).alias("p"),
                    (pl.col(name[1]) * scaling).alias("q"),
                )

            self.num_models.setdefault(model, 0)
            eid = f"{model}-{self.num_models[model]}"
            self.num_models[model] += 1

            self.models[eid] = self._create_data_model(
                data=cast(pl.LazyFrame, data),
                data_step_size=self.data_step_size,
                scaling=scaling,
                calculate_missing=calculate_missing,
                p_calculated=p_calculated,
                q_calculated=q_calculated,
                seed=self.rng.integers(self.seed_max),
                interpolate=self.interpolate,
                randomize_data=self.randomize_data,
                randomize_cos_phi=self.randomize_cos_phi,
            )

            entities.append({"eid": eid, "type": model})

        return entities

    def step(self, time, inputs, max_advance=0):
        """Perform a simulation step."""
        self.sim_time = time

        # Default inputs
        for model in self.models.values():
            model.cos_phi = self.cos_phi
            model.now_dt = self.now_dt

        # Inputs from other simulators
        for eid, attrs in inputs.items():
            log_msg = {
                "id": f"{self.sid}.{eid}",
                "name": eid,
                "type": eid.split("-")[1],
                "sim_time": self.sim_time,
                "msg_type": "input",
                "src_eids": [],
            }

            for attr, src_ids in attrs.items():
                setpoint = 0.0
                all_none = True
                for src_id, value in src_ids.items():
                    if value is not None:
                        all_none = False
                        setpoint += float(value)
                        log_msg["src_eids"].append(src_id)
                if not all_none:
                    log_msg[attr] = setpoint
                    setattr(self.models[eid], attr, setpoint)

            log_msg["src_eids"] = list(set(log_msg["src_eids"]))
            LOG.info(json.dumps(log_msg))

        # Step the models
        for model in self.models.values():
            model.step()

        self.now_dt += timedelta(seconds=self.step_size)

        return time + self.step_size

    def get_data(self, outputs):
        """Returns the requested outputs (if feasible)."""

        data = {}

        for eid, attrs in outputs.items():
            log_msg = {
                "id": f"{self.sid}.{eid}",
                "name": eid,
                "type": eid.split("-")[0],
                "sim_time": self.sim_time,
                "msg_type": "output",
            }
            data[eid] = {}
            for attr in attrs:
                data[eid][attr] = getattr(self.models[eid], attr)
                log_msg[attr] = getattr(self.models[eid], attr)

            LOG.info(json.dumps(log_msg))

        return data

    def get_data_info(self, eid=None):
        if eid is not None:
            return self.models[eid].p_mwh_per_a
        else:
            info = {
                key: {"p_mwh_per_a": model.p_mwh_per_a}
                for key, model in self.models.items()
            }
            info["num"] = {}
            for name, num in self.data_column_usage.items():
                info["num"][name] = num
            # info["num_lands"] = self.num_models.get("Land", 0)
            # info["num_households"] = self.num_models.get("Household", 0)
            return info


if __name__ == "__main__":
    set_and_init_logger(0, "sndata-logfile", "midas-sndata.log", replace=True)
    LOG.info("Starting mosaik simulation...")
    mosaik_api_v3.start_simulation(PowerSeriesSimulator())
