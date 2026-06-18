import json
from pathlib import Path


DEFAULT_CONFIG = {
    "race_count": 99,
    "buy_count": 30,
    "cj_count": 30,
    "sc_count": 30,
    "chk_1": True,
    "chk_2": True,
    "chk_3": True,
    "chk_4": True,
    "next_1": 2,
    "next_2": 3,
    "next_3": 4,
    "next_4": 1,
    "global_loops": 10,
    "skill_dirs": ["right", "up", "up", "up", "left"],
    "share_code": "890169683",
    "auto_restart": False,
    "restart_cmd": "start steam://run/2483190",
    "sell_mode": 1,
    "cj_mode": 1,
    "auto_close_game": False,
    "auto_shutdown": False,
    "use_ocr": False,
    "ocr_lang": "简体中文",
    "calc_a": "",
    "calc_b": "81700",
    "calc_c": "30",
    "start_hotkey": "F7",
    "stop_hotkey": "F8",
    "hotkey_start_task": "race",
}


def project_root(start=None):
    current = Path(start or __file__).resolve()
    if current.is_file():
        current = current.parent

    for parent in (current, *current.parents):
        if (parent / "main.py").is_file():
            return parent

    return Path.cwd()


def config_path(root=None):
    return Path(root or project_root()) / "config.json"


def normalize_config(raw):
    config = dict(DEFAULT_CONFIG)
    if isinstance(raw, dict):
        config.update(raw)

    for key in ("race_count", "buy_count", "cj_count", "sc_count", "global_loops"):
        config[key] = _int_in_range(config.get(key), DEFAULT_CONFIG[key], 0 if key != "global_loops" else 1, 999)

    for key in ("next_1", "next_2", "next_3", "next_4"):
        config[key] = _int_in_range(config.get(key), DEFAULT_CONFIG[key], 1, 4)

    for key in ("chk_1", "chk_2", "chk_3", "chk_4", "auto_restart", "auto_close_game", "auto_shutdown", "use_ocr"):
        config[key] = bool(config.get(key))

    config["sell_mode"] = 2 if str(config.get("sell_mode")) == "2" else 1
    config["cj_mode"] = 2 if str(config.get("cj_mode")) == "2" else 1
    config["share_code"] = _digits(config.get("share_code"), DEFAULT_CONFIG["share_code"])
    config["restart_cmd"] = str(config.get("restart_cmd") or DEFAULT_CONFIG["restart_cmd"]).strip()
    config["ocr_lang"] = str(config.get("ocr_lang") or DEFAULT_CONFIG["ocr_lang"]).strip()
    config["calc_a"] = _digits(config.get("calc_a"), "")
    config["calc_b"] = _digits(config.get("calc_b"), DEFAULT_CONFIG["calc_b"])
    config["calc_c"] = _digits(config.get("calc_c"), DEFAULT_CONFIG["calc_c"])
    config["start_hotkey"] = str(config.get("start_hotkey") or DEFAULT_CONFIG["start_hotkey"]).strip().upper()
    config["stop_hotkey"] = str(config.get("stop_hotkey") or DEFAULT_CONFIG["stop_hotkey"]).strip().upper()
    config["hotkey_start_task"] = str(config.get("hotkey_start_task") or DEFAULT_CONFIG["hotkey_start_task"]).strip().lower()
    if config["hotkey_start_task"] not in {"race", "buy", "cj", "sell"}:
        config["hotkey_start_task"] = DEFAULT_CONFIG["hotkey_start_task"]

    skill_dirs = config.get("skill_dirs")
    if not isinstance(skill_dirs, list):
        skill_dirs = DEFAULT_CONFIG["skill_dirs"]
    config["skill_dirs"] = [
        item for item in (str(x).strip().lower() for x in skill_dirs)
        if item in {"up", "down", "left", "right"}
    ]

    return config


def load_config(path=None):
    path = Path(path or config_path())
    if not path.exists():
        return dict(DEFAULT_CONFIG)

    with path.open("r", encoding="utf-8-sig") as f:
        return normalize_config(json.load(f))


def save_config(config, path=None):
    path = Path(path or config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_config(config)
    with path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=4, ensure_ascii=False)
    return normalized


def ensure_config_file(path=None):
    path = Path(path or config_path())
    if path.exists():
        return load_config(path)
    return save_config(dict(DEFAULT_CONFIG), path)


def _int_in_range(value, fallback, minimum, maximum):
    try:
        parsed = int(value)
    except Exception:
        parsed = fallback
    return max(minimum, min(maximum, parsed))


def _digits(value, fallback):
    result = "".join(ch for ch in str(value or "") if ch.isdigit())
    return result if result else fallback
