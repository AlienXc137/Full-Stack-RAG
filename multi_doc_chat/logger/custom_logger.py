import os
import logging
from datetime import datetime
import structlog


class CustomLogger:
    # Creates a folder called logs/ in your project directory
    # Generates a log file name like: logs/10_08_2025_01_25_36.log and Saves the full path in self.log_file_path.
    def __init__(self, log_dir="logs"):
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.logs_dir, log_file)

    # Takes an optional name (usually the filename using the logger) to tag log entries.
    # Example: If called from main.py, the logger will be named "main.py".
    def get_logger(self, name=__file__):
        logger_name = os.path.basename(name) # Extracts just the filename from the path

        #F ileHandler: writes logs to the .log file
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # StreamHandler: prints logs to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        # This initializes Python’s logging module so it uses both handlers simultaneously.
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[console_handler, file_handler]
        )

        # This tells structlog:
        # Add a timestamp in ISO format (2025-10-08T19:35:02Z)
        # Add a log level (e.g., "info")
        # Rename the main message field to "event"
        # Render the whole log as a JSON object
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger(logger_name)
    
# Example usage:
# logger = CustomLogger().get_logger(__name__)
# logger.info("Started retrieval pipeline")
# logger.warning("Missing embedding model, using default")
# logger.error("Failed to connect to database")
