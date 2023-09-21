"""
This module contains the ConfigManager class, which is a singleton class that manages the configuration of the application.
It loads environment variables and sets them as attributes of the ConfigManager instance. It also initializes the logger with the attributes of the ConfigManager instance.
It loads the detection configuration from a file and sets the attributes of the ConfigManager instance.
"""
import os
from ..common.Logger import Logger
from .AmqpConfig import AmqpConfig
from .DetectionConfig import DetectionConfig


class ConfigManager:
    """
    Singleton class that manages the configuration of the application.
    """

    _instance = None

    def __new__(cls):
        """
        Creates a new instance of the ConfigManager class if it does not exist.
        """
        if not cls._instance:
            # Initialize the class instance
            cls._instance = super(ConfigManager, cls).__new__(cls)

            # Put any initialization here.
            cls.__service_name = None
            cls.__version = None
            cls.__metrics_port = None
            cls.__log_level = None
            cls.__env = None
            cls.__detection_config_file_path = None
            cls.__segmentation_config_file_path = None  # not used
            cls.__logger = None
            # End of initialization section

            # Load configs
            cls._instance._load_environment()
            cls._instance._init_logger()
            cls.__amqp_config = AmqpConfig()
            cls._instance._load_detection_config()
            # End of loading configs

            cls._instance.__logger.debug("ConfigManager init completed",
                                         service_name=cls._instance.__service_name,
                                         version=cls._instance.__version,
                                         metrics_port=cls._instance.__metrics_port,
                                         log_level=cls._instance.__log_level,
                                         env=cls._instance.__env,
                                         detection_config_file_path=cls._instance.__detection_config_file_path,
                                         segmentation_config_file_path=cls._instance.__segmentation_config_file_path
                                         )
        return cls._instance

    def _load_environment(self):
        """
        Loads environment variables and sets them as attributes of the ConfigManager instance.
        """
        self.__service_name = os.getenv("APP_NAME", "livestream-ai-worker")
        self.__version = os.getenv("VERSION", "dev-version")
        self.__metrics_port = os.getenv("METRICS_PORT", 8000)
        self.__log_level = os.getenv("LOG_LEVEL", "debug")
        self.__env = os.getenv("ENVIRONMENT", "dev")
        self.__detection_config_file_path = os.getenv(
            "DETECTION_CONFIG_FILE_PATH", "configs/detection_nvinfer.txt")
        self.__segmentation_config_file_path = os.getenv(
            "SEGMENTATION_CONFIG_FILE_PATH", "configs/segmentation_nvinfer.txt")
        self.__batch_size = os.getenv("DETECTION_BATCH_SIZE", 10)
        self.__gpu_id = os.getenv("DETECTION_GPU_ID", "0")

    def _init_logger(self):
        """
        Initializes the logger with the attributes of the ConfigManager instance.
        """
        self.__logger = Logger().init(
            log_level=self.__log_level, app_name=self.__service_name, app_version=self.__version, environment=self.__env
        ).get_logger()

    def _load_detection_config(self):
        """
        Loads the detection configuration from a file.
        """
        self.__detection_config = DetectionConfig(
            nvinfer_config_file_path=self.__detection_config_file_path,
            batch_size=self.__batch_size,
            gpu_id=self.__gpu_id
        )
        self.__detection_config.build_config()

    def get_logger_level(self):
        """
        Returns the log level attribute of the ConfigManager instance.
        """
        return self.__log_level

    def get_app_version(self):
        """
        Returns the app version attribute of the ConfigManager instance.
        """
        return self.__version

    def get_app_name(self):
        """
        Returns the app name attribute of the ConfigManager instance.
        """
        return self.__service_name

    def get_environment(self):
        """
        Returns the environment attribute of the ConfigManager instance.
        """
        return self.__env

    def get_metrics_port(self):
        """
        Returns the metrics port attribute of the ConfigManager instance.
        """
        return self.__metrics_port

    def get_detection_config_file_path(self):
        """
        Returns the detection config file path attribute of the ConfigManager instance.
        """
        return self.__detection_config_file_path

    def get_segmentation_config_file_path(self):
        """
        Returns the segmentation config file path attribute of the ConfigManager instance.
        """
        return self.__segmentation_config_file_path

    def get_amqp_config(self):
        """
        Returns the AMQP config attribute of the ConfigManager instance.
        """
        return self.__amqp_config
