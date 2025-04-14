import asyncio
import logging.config
import os
import sys

import yaml

from dotenv import load_dotenv
from flask import Flask

from app.consts import (
    APP_CONFIG_BY_ENV_PATH,
    ENV_FLASK_ENV,
    ENV_JWT_SECRET,
    LOGS_CONFIG_PATH,
)

# creating FLASK app
app = Flask(__name__)

# Loading environment
load_dotenv()
env = os.getenv(ENV_FLASK_ENV)


# logging configuration
with open(LOGS_CONFIG_PATH, mode="r", encoding="utf-8") as f_cfg:
    log_config = yaml.safe_load(f_cfg.read())
    logs_output_folder = (
        log_config.get("handlers", {})
        .get("info_file_handler", {})
        .get("filename", None)
    )
    # Loading logs output folder from logging configuration
    # to prevent manual specifying of log output folder
    logs_output_folder = (
        logs_output_folder.split("/")[1]
        if logs_output_folder
        and isinstance(logs_output_folder, list)
        and len(logs_output_folder) == 2
        else "logs"
    )

os.makedirs(logs_output_folder, exist_ok=True)
logging.config.dictConfig(log_config)

logger = logging.getLogger(__name__)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
