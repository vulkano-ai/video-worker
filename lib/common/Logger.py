import structlog
import logging


import structlog
import logging


class Logger:
    """
    A singleton logger class that provides a structured logging interface using structlog.
    """
    _instance = None

    def __new__(cls):
        """
        Creates a new instance of the Logger class if it doesn't exist already.

        Returns:
            The Logger instance.
        """
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
            cls.log_level = "INFO"
            cls.app_name = None
            cls.app_version = None
            cls.environment = None
            cls.log_json_format = False
        return cls._instance

    def init(self, log_level="info", app_name="livestream-ai-worker", app_version="v.1.0.0", environment="dev"):
        """
        Initializes the Logger instance.

        Args:
            log_level (str): The log level to use for the logger. Defaults to "info".
            app_name (str): The name of the application. Defaults to "livestream-ai-worker".
            app_version (str): The version of the application. Defaults to "v.1.0.0".
            environment (str): The environment the application is running in. Defaults to "dev".
        """
        self.log_level = log_level.upper()
        self.app_name = app_name
        self.app_version = app_version
        self.environment = environment
        self.log_json_format = environment in ["prod", "stg"]
        self._configure_logging()
        return self

    def _configure_logging(self):
        """
        Configures the logging for the Logger instance using structlog.
        """
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(
                ) if self.log_json_format else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            cache_logger_on_first_use=True,
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.getLevelName(self.log_level)),
        )

        logging.basicConfig(level=self.log_level)

    def get_logger(self, context=None):
        """
        Returns a logger instance with the specified context.

        Args:
            context (str): The context for the logger. Defaults to "main".

        Returns:
            The logger instance.
        """
        logger = structlog.get_logger()
        logger = logger.bind(
            service=self.app_name,
            version=self.app_version,
            env=self.environment,
            context=context if context is not None else "main"
        )
        return logger

    def update_logger_level(self, log_level):
        """
        Updates the log level for the Logger instance.

        Args:
            log_level (str): The new log level to use.
        """
        self._instance.log_level = log_level.upper()
        self._configure_logging()
        self.get_logger().info("Updated log level to: {}".format(log_level))

    def set_log_level(self, log_level):
        """
        Updates the log level for the Logger instance.

        Args:
            log_level (str): The new log level to use.
        """
        self._instance.log_level = log_level.upper()
        self._configure_logging()
        self.get_logger().info("Updated log level to: {}".format(log_level))

    def get_log_level(self):
        """
        Returns the log level for the Logger instance.

        Returns:
            The log level.
        """
        return self._instance.log_level

    def set_app_name(self, app_name):
        """
        Updates the app name for the Logger instance.

        Args:
            app_name (str): The new app name to use.
        """
        self._instance.app_name = app_name
        self.get_logger().info("Updated app name to: {}".format(app_name))

    def get_app_name(self):
        """
        Returns the app name for the Logger instance.

        Returns:
            The app name.
        """
        return self._instance.app_name

    def set_app_version(self, app_version):
        """
        Updates the app version for the Logger instance.

        Args:
            app_version (str): The new app version to use.
        """
        self._instance.app_version = app_version
        self.get_logger().info("Updated app version to: {}".format(app_version))

    def get_app_version(self):
        """
        Returns the app version for the Logger instance.

        Returns:
            The app version.
        """
        return self._instance.app_version

    def set_environment(self, environment):
        """
        Updates the environment for the Logger instance.

        Args:
            environment (str): The new environment to use.
        """
        self._instance.environment = environment
        self.get_logger().info("Updated environment to: {}".format(environment))

    def get_environment(self):
        """
        Returns the environment for the Logger instance.

        Returns:
            The environment.
        """
        return self._instance.environment
