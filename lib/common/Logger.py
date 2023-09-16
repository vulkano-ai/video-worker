import structlog
import logging


class Logger:
    _instance = None

    def __new__(cls, log_level="info", app_name="livestream-ai-worker", app_version="v.1.0.0", environment="dev"):
        if not cls._instance:
            print("Creating Logger, using log level: {}".format(log_level))
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.log_level = log_level.upper()
            cls._instance.app_name = app_name
            cls._instance.app_version = app_version
            cls._instance.environment = environment
            cls._instance.log_json_format = environment in ["prod", "stg"]
            cls._instance._configure_logging()
        return cls._instance

    def _configure_logging(self):
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer() if self.log_json_format else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            cache_logger_on_first_use=True,
            wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(self.log_level)),
        )

        logging.basicConfig(level=self.log_level)

    def get_logger(self, context=None):
        logger = structlog.get_logger()
        logger = logger.bind(
            service=self.app_name,
            version=self.app_version,
            env=self.environment,
            context=context if context is not None else "main"
        )
        return logger

    def update_logger_level(self, log_level):
        self._instance.log_level = log_level.upper()
        self._configure_logging()
        self.get_logger().info("Updated log level to: {}".format(log_level))
