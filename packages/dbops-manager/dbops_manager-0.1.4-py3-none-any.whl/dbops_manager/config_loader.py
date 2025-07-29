"""Configuration loader for PostgreSQL connections."""

import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

from .exceptions import ConfigurationError

# Configure logging
logger = logging.getLogger(__name__)

REQUIRED_CONFIG_KEYS = ['host', 'port', 'dbname', 'user', 'password']

def load_from_env(
    env_prefix: str = "DB_",
    logging_enabled: bool = False
) -> Dict[str, str]:
    """
    Load PostgreSQL configuration from environment variables.
    
    Args:
        env_prefix: Prefix for environment variables (default: "DB_")
        logging_enabled: Enable logging for configuration loading
    
    Returns:
        Dict containing PostgreSQL configuration
    
    Raises:
        ConfigurationError: If required configuration is missing
    """
    if logging_enabled:
        logger.info("Loading configuration from environment variables")
    
    load_dotenv()
    
    config = {
        'host': os.getenv(f"{env_prefix}HOST"),
        'port': os.getenv(f"{env_prefix}PORT", "5432"),
        'dbname': os.getenv(f"{env_prefix}NAME"),
        'user': os.getenv(f"{env_prefix}USER"),
        'password': os.getenv(f"{env_prefix}PASSWORD"),
        'sslmode': os.getenv(f"{env_prefix}SSLMODE", "prefer")
    }
    
    missing_keys = [key for key in REQUIRED_CONFIG_KEYS if not config.get(key)]
    if missing_keys:
        error_msg = f"Missing required PostgreSQL configuration: {', '.join(missing_keys)}"
        if logging_enabled:
            logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    if logging_enabled:
        logger.info("Successfully loaded configuration from environment")
        logger.debug("Configuration: %s", {k: '***' if k == 'password' else v for k, v in config.items()})
    
    return config

def validate_config(
    config: Dict[str, str],
    logging_enabled: bool = False
) -> None:
    """
    Validate PostgreSQL configuration.
    
    Args:
        config: Configuration dictionary to validate
        logging_enabled: Enable logging for configuration validation
    
    Raises:
        ConfigurationError: If required configuration is missing
    """
    if logging_enabled:
        logger.info("Validating configuration")
    
    missing_keys = [key for key in REQUIRED_CONFIG_KEYS if not config.get(key)]
    if missing_keys:
        error_msg = f"Missing required PostgreSQL configuration: {', '.join(missing_keys)}"
        if logging_enabled:
            logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    if logging_enabled:
        logger.info("Configuration validation successful")
        logger.debug("Configuration: %s", {k: '***' if k == 'password' else v for k, v in config.items()}) 