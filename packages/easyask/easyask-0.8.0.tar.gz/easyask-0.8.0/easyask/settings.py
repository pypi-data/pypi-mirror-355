import logging
import os

from pydantic_settings import BaseSettings  # 新的导入
from pydantic_settings.sources import DotenvType

logger = logging.getLogger(__name__)


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Settings(BaseSettings):
    def __init__(self, env_file: DotenvType):
        super().__init__(_env_file=env_file)

    host: str
    port: int

    dashscope_api_key: str


def get_settings():
    env = os.getenv("ENV", "local")
    additional_config_dir = os.getenv("ADDITIONAL_CONFIG_DIR", None)
    env_file = f".env.{env.lower()}"

    if additional_config_dir:
        env_file = os.path.join(additional_config_dir, env_file)
    else:
        env_file = os.path.join(os.getcwd(), env_file)

    logger.info(f"[settings] loading environment file: {env_file}")
    return Settings(env_file=env_file)
