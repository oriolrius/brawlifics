import logging
import logging.config
import yaml
import os


def setup_logger():
    config_path = os.path.join("etc", "logging.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Configure logging using the YAML configuration
    logging.config.dictConfig(config)

    # Get the logger instance for 'lib'
    return logging.getLogger("lib")


# Create a singleton logger instance
logger = setup_logger()
