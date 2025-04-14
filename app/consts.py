import os
from pathlib import Path

ENV_FLASK_ENV = "FLASK_ENV"
ENV_JWT_SECRET = "JWT_SECRET"
ENV_ES_TOKEN = "ES_TOKEN"

ENV_MAPPER = {"development": "dev", "cloud": "cloud"}

ALLOWED_FLASK_ENV = tuple(ENV_MAPPER.keys())

APP_CONFIG_BY_ENV_PATH = lambda: Path(
    "config/app.config.{}.yaml".format(ENV_MAPPER.get(os.getenv(ENV_FLASK_ENV)))
)
APP_CONFIG_PATH = lambda: Path("config/app.config.yaml")
LOGS_CONFIG_PATH = Path("config/log.config.yaml")
