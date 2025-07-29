# config/logging_config.py

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG":    "cyan",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "color",
            "level": "DEBUG",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },

    "loggers": {
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False
        },
        "uvicorn": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False
        },
        "apscheduler": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
    }
}
