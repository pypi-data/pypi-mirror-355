import csv
import json
import logging
import os
from importlib import import_module
from typing import Any, Dict, cast

from midas.scenario.upgrade_module import (
    ModuleParams,
    TimeSeriesMapping,
    UpgradeModule,
)
from midas.util.dict_util import (
    set_default_bool,
    set_default_float,
    set_default_int,
)

from .meta import ATTRIBUTE_MAP

LOG = logging.getLogger(__name__)


class PowerSeriesModule(UpgradeModule):
    def __init__(
        self,
        module_name="powerseries",
        default_scope_name="midasmv",
        default_sim_config_name="PowerSeriesData",
        default_import_str="midas_powerseries.simulator:PowerSeriesSimulator",
        default_cmd_str="%(python)s -m midas_powerseries.simulator %(addr)s",
        default_connect_str="localhost:59998",
        log=LOG,
    ):
        super().__init__(
            module_name,
            default_scope_name,
            default_sim_config_name,
            default_import_str,
            default_cmd_str,
            log,
        )

        self.models = {}
        for entity, data in ATTRIBUTE_MAP.items():
            self.models.setdefault(entity, [])
            for attr in data:
                # for attr in attrs:
                self.models[entity].append(attr)
        self._models_started = {}

    def check_module_params(self, mp: ModuleParams) -> None:
        """Check the module params and provide default values

        This module can take the following inputs:

        meta_scaling: float
            This is intended to be used in the scenario configuration
            to scale all the models by the same value. Defaults to 1
        data_scaling: float
            This is intended to be used by subclasses to make sure that
            the data is in the dimension of mega watts. Defaults to 1

        """

        mp.setdefault("start_date", self.scenario.base.start_date)
        mp.setdefault("data_path", self.scenario.base.data_path)
        set_default_float(mp, "cos_phi", self.scenario.base.cos_phi)
        set_default_bool(mp, "calculate_missing_power", True)
        set_default_bool(mp, "use_custom_time_series", False)
        set_default_bool(mp, "is_load", True)
        set_default_bool(mp, "is_sgen", False)
        set_default_bool(mp, "interpolate", False)
        set_default_float(mp, "noise_factor", 0.2)
        set_default_float(mp, "meta_scaling", 1.0)
        set_default_float(mp, "data_scaling", 1.0)

        if mp["no_rng"]:
            mp["randomize_data"] = False
            mp["randomize_cos_phi"] = False
        else:
            set_default_bool(mp, "randomize_data")
            set_default_bool(mp, "randomize_cos_phi")

    def check_sim_params(self, mp: ModuleParams) -> None:
        """Check the params for a certain scope/simulator instance.

        This functions checks the availability of required parameters
        and provides default values if necessary. Parameters that are
        checked are listed in the following:

        Attributes
        ----------
        grid_name: str
            The scope name for this simulator inside the module.
            Expects to have a same-named grid_name of the powergrid
            module.

        start_date: str
            ISO date string containing the starting time of the
            simulator. If not specified, it will be derived from the
            module params.

        data_path: str
            The path where the simulator should look for data.
            If not specified, it will be derived from the module
            params.

        cos_phi: float
            The cos phi for this simulator to use whenever cos phi is
            required to calculate a (missing) power value. If not
            specified, it will be derived from the module params.

        calculate_missing_power: bool
            If set to True, missing power will be calculated if an
            appropiate model is chosen, i.e., if an active_mapping
            is used to define models, CalculatedQTimeSeries will be
            created. Otherwise, missing power will not be calculated,
            i.e., an ActiveTimeSeries model will be created.

        is_load: bool
            Set to specify if this simulator hosts load time series.
            If both is_load and is_sgen is set to True, the model will
            be treated as Storage. If both are set to False, it will
            be attempted to derive the type from the name, i.e.,
            something with `load` in the name will be treated as load
            and so on.

        is_sgen: bool
            Similar to `is_load` but for generation time series.

        """

        self.sim_params.setdefault("grid_name", self.scope_name)
        self._simp_from_modulep(mp, "start_date")
        self._simp_from_modulep(mp, "data_path")
        self._simp_from_modulep(mp, "cos_phi", dtype="float")
        self._simp_from_modulep(mp, "calculate_missing_power", dtype="bool")
        self._simp_from_modulep(mp, "is_load", dtype="bool")
        self._simp_from_modulep(mp, "is_sgen", dtype="bool")
        self._simp_from_modulep(mp, "interpolate", dtype="bool")
        self._simp_from_modulep(mp, "randomize_data", dtype="bool")
        self._simp_from_modulep(mp, "randomize_cos_phi", dtype="bool")
        self._simp_from_modulep(mp, "noise_factor", dtype="float")
        self._simp_from_modulep(mp, "meta_scaling", dtype="float")
        self._simp_from_modulep(mp, "data_scaling", dtype="bool")
        self._simp_from_modulep(mp, "use_custom_time_series", dtype="bool")

        set_default_int(self.sim_params, "seed", self.scenario.create_seed())
        set_default_int(
            self.sim_params, "seed_max", self.scenario.base.seed_max
        )

        self.sim_params.setdefault("active_mapping", {})
        self.sim_params.setdefault("reactive_mapping", {})
        self.sim_params.setdefault("combined_mapping", {})
        # self.sim_params.setdefault("default_mapping", {})
        self.sim_params.setdefault("aliases", {})

        self.sim_params.setdefault("active_mapping_filename", "")
        self.sim_params.setdefault("reactive_mapping_filename", "")
        self.sim_params.setdefault("combined_mapping_filename", "")
        self.sim_params.setdefault("aliases_filename", "")
        set_default_bool(
            self.sim_params, "prefer_active_mapping_from_file", False
        )
        set_default_bool(
            self.sim_params, "prefer_reactive_mapping_from_file", False
        )
        set_default_bool(
            self.sim_params, "prefer_combined_mapping_from_file", False
        )

        self._load_mapping("active_mapping")
        self._load_mapping("reactive_mapping")
        self._load_mapping("combined_mapping")

    def _load_mapping(self, mapping_name: str):
        mapping_filename: str = cast(
            str, self.sim_params[f"{mapping_name}_filename"]
        )
        mapping_flag = cast(
            bool, self.sim_params[f"prefer_{mapping_name}_from_file"]
        )
        if mapping_flag or not cast(
            TimeSeriesMapping, self.sim_params[mapping_name]
        ):
            if mapping_filename:
                path = os.path.abspath(
                    os.path.join(
                        cast(str, self.sim_params["data_path"]),
                        mapping_filename,
                    )
                )
                if mapping_filename.endswith(".json"):
                    mapping = self._load_mapping_from_json(path)
                elif mapping_filename.endswith(".csv"):
                    mapping = self._load_mapping_from_csv(path)
                else:
                    LOG.warning(
                        "Loading mappings from %s files is not supported",
                        mapping_filename.rsplit(".", 1)[1],
                    )
                    mapping = None
            else:
                mapping = None

            if mapping is not None:
                self.sim_params[mapping_name] = mapping

    def _load_mapping_from_json(self, filename: str) -> TimeSeriesMapping:
        try:
            with open(filename, "r") as json_file:
                json_mapping = json.load(json_file)
            mapping = {}
            for key, val in json_mapping.items():
                mapping[int(key)] = val
        except Exception:
            LOG.exception(
                "Could not load mapping from %s. Will use an empty "
                "mapping instead! ",
                filename,
            )
            mapping = {}
        return mapping

    def _load_mapping_from_csv(self, filename: str) -> TimeSeriesMapping:
        try:
            csv_content = []
            with open(filename, "r") as csv_file:
                reader = csv.reader(csv_file)
                for idx, row in enumerate(reader):
                    csv_content.append(row)

            csv_mapping = {}
            for idx, col in enumerate(csv_content[0]):
                csv_mapping[col] = []
                for row in csv_content[1:]:
                    val = row[idx]
                    try:
                        val = int(val)
                    except Exception:
                        try:
                            val = float(val)
                        except Exception:
                            pass
                    csv_mapping[col].append(val)

            mapping = {}
            for value in csv_mapping["bus"]:
                mapping.setdefault(value, [])

            for bus, mod1, mod2, scaling in zip(
                csv_mapping["bus"],
                csv_mapping["model_1"],
                csv_mapping["model_2"],
                csv_mapping["scaling"],
            ):
                if mod2:
                    model = [mod1, mod2]
                else:
                    model = mod1

                mapping[bus].append([model, scaling])

        except Exception:
            LOG.exception(
                "Could not load mapping from %s. Will use an empty "
                "mapping instead! ",
                filename,
            )
            mapping = {}
        return mapping

    def start_models(self):
        self._models_started = {}

        if self.sim_params["is_load"] and self.sim_params["is_sgen"]:
            mtype = "storage"
        elif self.sim_params["is_load"]:
            mtype = "load"
        elif self.sim_params["is_sgen"]:
            mtype = "sgen"
        else:
            # Derive from name
            mtype = "combined"

        mapping = self.scenario.create_shared_mapping(
            self, cast(str, self.sim_params["grid_name"]), mtype
        )

        if ":" in self.default_import_str:
            mod, clazz = self.default_import_str.split(":")
        else:
            mod, clazz = self.default_import_str.rsplit(".", 1)
        mod = import_module(mod)

        sim_dummy = getattr(mod, clazz)()
        sim_dummy.init(self.sid, **self.sim_params)

        if self.sim_params["use_custom_time_series"]:
            model_name = "CustomTimeSeries"
        elif self.sim_params["calculate_missing_power"]:
            model_name = "CalculatedQTimeSeries"
        else:
            model_name = "ActiveTimeSeries"

        self._start_models_from_mapping(
            "active_mapping", mapping, model_name, sim_dummy, mtype
        )

        if self.sim_params["use_custom_time_series"]:
            model_name = "CustomTimeSeries"
        elif self.sim_params["calculate_missing_power"]:
            model_name = "CalculatedPTimeSeries"
        else:
            model_name = "ReactiveTimeSeries"
        self._start_models_from_mapping(
            "reactive_mapping", mapping, model_name, sim_dummy, mtype
        )

        if self.sim_params["use_custom_time_series"]:
            model_name = "CustomTimeSeries"
        else:
            model_name = "CombinedTimeSeries"

        self._start_models_from_mapping(
            "combined_mapping", mapping, model_name, sim_dummy, mtype
        )

    def _start_models_from_mapping(
        self, mapping_name, shared_mapping, model_name, sim_dummy, mtype
    ):
        determine_mtype = mtype == "combined"
        mapping = cast(TimeSeriesMapping, self.sim_params[mapping_name])
        for bus, entities in mapping.items():
            shared_mapping.setdefault(bus, [])
            for eidx, (col_id, scaling) in enumerate(entities):
                if isinstance(col_id, list):
                    col_id, col_id2 = col_id
                else:
                    col_id2 = None
                assert isinstance(col_id, str)
                if determine_mtype:
                    if "load" in col_id.lower():
                        mtype = "load"
                    elif "sgen" in col_id.lower():
                        mtype = "sgen"
                    else:
                        if "storage" not in col_id.lower():
                            LOG.info(
                                "Could determine model type for %s. "
                                "Will default to 'storage'.",
                                col_id,
                            )
                        mtype = "storage"
                model_key = self.scenario.generate_model_key(
                    self, model_name, str(bus), str(eidx)
                )
                scaling *= cast(float, self.sim_params["meta_scaling"]) * cast(
                    float, self.sim_params["data_scaling"]
                )
                if col_id2 is not None:
                    col_id = [col_id, col_id2]

                params = {"name": col_id, "scaling": scaling}
                entity = sim_dummy.create(1, model_name, **params)[0]
                self.start_model(model_key, entity["type"], params)

                shared_mapping[bus].append(
                    (
                        model_name,
                        sim_dummy.get_data_info(entity["eid"]),
                        f"{self.sid}.{entity['eid']}",
                    )
                )
                self._models_started[model_key] = {
                    "bus": bus,
                    "type": mtype,
                    "model": model_name,
                }

    def connect(self):
        no_grid_warning = True
        for model_key, info in self._models_started.items():
            if info["bus"] == -1 and "no_grid" in cast(
                str, self.sim_params["grid_name"]
            ):
                # We really don't want to use a grid
                if no_grid_warning:
                    LOG.info(
                        "Will start without connecting to grid because models "
                        "are assigned to bus -1 and 'no_grid' is part of the "
                        "grid name!"
                    )
                    no_grid_warning = False
                continue
            grid_entity_key = self.get_grid_entity(info["type"], info["bus"])
            attrs = [
                attr[0]
                for attr in self.models[info["model"]]
                if "output" in attr
            ]
            self.connect_entities(model_key, grid_entity_key, attrs)

    def connect_to_db(self):
        db_entity_key = self.scenario.find_first_model("store", "database")[0]
        if db_entity_key is None:
            msg = "Could not find database in the scenario."
            raise ValueError(msg)
        for model_key, info in self._models_started.items():
            attrs = [
                attr[0]
                for attr in self.models[info["model"]]
                if "output" in attr
            ]
            self.connect_entities(model_key, db_entity_key, attrs)

    def get_grid_entity(self, mtype, bus, eidx=None):
        endswith = f"{eidx}_{bus}" if eidx is not None else f"_{bus}"
        models = self.scenario.find_grid_entities(
            self.sim_params["grid_name"], mtype, endswith=endswith
        )
        if models:
            for key in models:
                # Return first match
                return key

        self.logger.info(
            "Grid entity for %s, %s at bus %d not found",
            self.sim_params["grid_name"],
            mtype,
            bus,
        )

        raise ValueError(
            f"Grid entity for {self.sim_params['grid_name']}, {mtype} "
            f"at bus {bus} not found!"
        )
