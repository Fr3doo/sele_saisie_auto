import configparser
import importlib
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import logger_utils  # noqa: E402


def test_initialize_logger_override(tmp_path):
    mod = importlib.reload(logger_utils)
    cfg = configparser.ConfigParser()
    cfg['settings'] = {'debug_mode': 'INFO'}
    mod.initialize_logger(cfg, log_level_override='DEBUG')
    assert mod.LOG_LEVEL_FILTER == 'DEBUG'
