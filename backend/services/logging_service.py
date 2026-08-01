import logging
import logging.config
import yaml
from pathlib import Path
from config.settings import settings

def setup_logging():
    """Initializes logging from the YAML configuration."""
    try:
        config_path = Path(settings.LOG_CONFIG_PATH)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=logging.INFO)
            logging.warning("logging.yaml not found. Using basic console logging.")
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to load logging config: {e}")

def get_logger(name: str) -> logging.Logger:
    """
    Shared logging interface for all backend modules.
    Usage: logger = get_logger(__name__)
    """
    return logging.getLogger(name)