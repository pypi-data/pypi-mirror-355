from typing import Any, Optional, Tuple

import datetime
from logging import Logger
from logging import config as logging_config
from logging import getLogger
from pathlib import Path

import yaml

from .config import CONFIG_DIR


def get_loggers(module_path: Path,
                logging_yaml: Path,
                logger_name: Optional[str] = None
                ) -> Tuple[Logger, Optional[Path]]:
    """
    Create a logger out of yaml log configuration.
    :returns: log and path to alarm log file
    """
    _log_config = yaml.safe_load(logging_yaml.read_text().format(
        now=datetime.datetime.now(datetime.UTC),
        CONFIG_DIR=CONFIG_DIR,
    ))
    alarm_log = None
    if 'alert' in _log_config['handlers']:
        alarm_log = Path(_log_config['handlers']['alert']['filename'])

    logging_config.dictConfig(_log_config)

    return getLogger(logger_name or module_path.name), alarm_log


class MakeRetryAsInfo(Logger):
    """
    Wrapper for retry lib how retry times in logs
    """
    def warning(self, *args: Any, **kwargs: Any) -> None:
        print("MY_INFO ====== ", *args, **kwargs)
        super().info(*args, **kwargs)
