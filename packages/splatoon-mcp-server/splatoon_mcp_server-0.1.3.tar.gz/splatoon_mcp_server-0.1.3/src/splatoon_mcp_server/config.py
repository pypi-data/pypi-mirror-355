"""Configuration settings for the splatoon MCP server."""

import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Server configuration settings."""

    APP_NAME: str = "splatoon-mcp-server"  # 修改为你的项目名称
    APP_VERSION: str = "0.1.2"            # 修改为 pyproject.toml 中的版本号（0.1.2）
    MAX_RESULTS: int = 50                 # 可根据实际需求调整数值
    BATCH_SIZE: int = 20
    REQUEST_TIMEOUT: int = 60
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    model_config = SettingsConfigDict(extra="allow")