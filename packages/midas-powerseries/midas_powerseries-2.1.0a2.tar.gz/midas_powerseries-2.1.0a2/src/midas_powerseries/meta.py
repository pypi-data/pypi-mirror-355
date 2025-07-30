import numpy as np

ATTRIBUTE_MAP = {
    "CalculatedQTimeSeries": [
        ("p_mw", "float", 0, np.inf, "output"),
        ("q_mvar", "float", -np.inf, np.inf, "output"),
        ("p_set_mw", "float", 0, np.inf, "input"),
        ("q_set_mw", "float", -np.inf, np.inf, "input"),
    ],
    "CalculatedPTimeSeries": [
        ("p_mw", "float", 0, np.inf, "output"),
        ("q_mvar", "float", -np.inf, np.inf, "output"),
        ("p_set_mw", "float", 0, np.inf, "input"),
        ("q_set_mw", "float", -np.inf, np.inf, "input"),
    ],
    "CombinedTimeSeries": [
        ("p_mw", "float", 0, np.inf, "output"),
        ("q_mvar", "float", -np.inf, np.inf, "output"),
        ("p_set_mw", "float", 0, np.inf, "input"),
        ("q_set_mw", "float", -np.inf, np.inf, "input"),
    ],
    "ActiveTimeSeries": [
        ("p_mw", "float", 0, np.inf, "output"),
        ("p_set_mw", "float", 0, np.inf, "input"),
    ],
    "ReactiveTimeSeries": [
        ("q_mvar", "float", -np.inf, np.inf, "output"),
        ("q_set_mw", "float", -np.inf, np.inf, "input"),
    ],
    "CustomTimeSeries": [
        ("p_mw", "float", 0, np.inf, "output"),
        ("q_mvar", "float", -np.inf, np.inf, "output"),
        ("p_set_mw", "float", 0, np.inf, "input"),
        ("q_set_mw", "float", -np.inf, np.inf, "input"),
    ],
}


META = {
    "type": "time-based",
    "models": {
        "CalculatedQTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["p_mw", "q_mvar", "p_set_mw", "q_set_mw"],
        },
        "CalculatedPTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["p_mw", "q_mvar", "p_set_mw", "q_set_mw"],
        },
        "CombinedTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["p_mw", "q_mvar", "p_set_mw", "q_set_mw"],
        },
        "ActiveTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["p_mw", "p_set_mw"],
        },
        "ReactiveTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["q_mvar", "q_set_mw"],
        },
        "CustomTimeSeries": {
            "public": True,
            "params": ["name", "scaling"],
            "attrs": ["p_mw", "q_mvar", "p_set_mw", "q_set_mw"]
        }
    },
    "extra_methods": ["get_data_info"],
}
