import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from prefy import Preferences

### BE SURE TO ADD log_file_name and app_name settings. Cf. settings_example.json

class MTKLogger(logging.Logger):
    def __init__(self, script_name=None, backup_count=7):
        settings = Preferences()
        
        log_file_name=settings.log_file_name
        app_name=settings.app_name

        # Set up base logger
        super().__init__(app_name)
        preferences_level=settings.log_level
        level = getattr(logging, preferences_level, logging.DEBUG)
        self.setLevel(level)

        # Common log file for the day
        log_filename = os.path.join(settings.log_dir, f'{log_file_name}.log')

        # Script name for contextual logging
        script_id = script_name or os.path.basename(sys.argv[0])

        # Custom formatter including script name
        formatter = logging.Formatter(
            f'%(asctime)s - %(name)s - %(levelname)s - {script_id} - [Line %(lineno)d] - %(message)s'
        )

        # Timed rotating file handler (daily, retain N days)
        file_handler = TimedRotatingFileHandler(
            filename=log_filename,
            when='midnight',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8',
            utc=False  # Use True if you want UTC timestamps
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

        self.debug("Logging initialized for script: %s, daily rotation enabled, logs in: %s", script_id, log_filename)

def get_logger(script_name=None, backup_count=7):
    return MTKLogger(script_name, backup_count)
