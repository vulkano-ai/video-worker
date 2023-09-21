import os
from ..common.Logger import Logger
from configparser import ConfigParser


class DetectionConfig:
    """
    A class used to represent the detection configuration for the PSM-DS Detector.

    Attributes
    ----------
    __nvinfer_config_file_path : str
        The path to the nvinfer configuration file.
    __config : ConfigParser
        The configuration parser object.
    __logger : Logger
        The logger object.
    __gpu_id : str
        The GPU ID to use for detection.
    __model_engine_file_path : str
        The path to the model engine file.
    __onnx_file_path : str
        The path to the ONNX file.
    __batch_size : int
        The batch size for detection.
    __custom_lib_path : str
        The path to the custom library.

    Methods
    -------
    get_config()
        Returns the configuration.
    build_config()
        Builds the configuration.
    """


class DetectionConfig:

    __nvinfer_config_file_path = None
    __config = None
    __logger = None

    __gpu_id = None
    __model_engine_file_path = None
    __onnx_file_path = None
    __batch_size = None
    __custom_lib_path = None

    def __init__(self, nvinfer_config_file_path, gpu_id="0", batch_size=10, custom_lib_path="/usr/local/lib/libnvdsinfer_yolo_v8.so"):
        """
        Initializes the DetectionConfig class.

        Args:
        nvinfer_config_file_path (str): The path to the nvinfer configuration file.
        gpu_id (str): The GPU ID to use for detection.
        batch_size (int): The batch size for detection.
        custom_lib_path (str): The path to the custom library.        
        """
        self.__logger = Logger().get_logger("DetectionConfig")
        self.__logger.debug("DetectionConfig init started")
        self.__nvinfer_config_file_path = nvinfer_config_file_path
        self.__gpu_id = gpu_id
        self.__custom_lib_path = custom_lib_path
        self.__batch_size = batch_size

        self.__load_detection_config_file()
        self.__logger.debug("DetectionConfig init completed")

    def __load_detection_config_file(self):
        """
        Loads the detection config file.
        """
        self.__logger.debug("Loading detection config file")
        self.__config = ConfigParser()
        self.__config.read(self.__nvinfer_config_file_path)
        self.__logger.debug("Loading detection config file completed")

    def build_config(self):
        """
        Builds the configuration file for object detection.

        Raises:
        ValueError: If the required configuration values are not present or invalid.
        """
        # check if parser has the required sections
        if "property" not in self.__config.sections():
            self.__config["property"] = {}
        if "class-attrs-all" not in self.__config.sections():
            self.__config["class-attrs-all"] = {}

        # checking required fields
        self.__check_required_config_value("property", "onnx-file")
        self.__onnx_file_path = self.__config["property"]["onnx-file"]
        self.__check_onnx_file()
        self.__build_engine_file_path()

        # build config
        self.__set_required_fields()
        self.__set_optional_fields()

        # write config
        self.__write_config_file()

    def __check_required_config_value(self, section, key):
        """
        Check if the required configuration value is present in the specified section.

        Args:
            section (str): The section in the configuration file to check.
            key (str): The key in the specified section to check.

        Raises:
            ValueError: If the specified key is not present in the specified section.
        """
        if key not in self.__config[section]:
            raise ValueError(
                "Invalid detection config file value: [{}] -> {}".format(section, key))

    def __override_config_field(self, section, key, value):
        """
        Overrides the value of a configuration field in the specified section.

        Args:
            section (str): The section in which the configuration field is located.
            key (str): The key of the configuration field to be overridden.
            value (str): The new value to be set for the configuration field.

        Returns:
            None
        """
        self.__config[section][key] = value

    def __add_config_field_if_not_exists(self, section, key, value):
        """
        Adds a new configuration field to the specified section if it does not already exist.

        Args:
            section (str): The section to add the configuration field to.
            key (str): The key of the configuration field to add.
            value (str): The value of the configuration field to add.
        """
        if key not in self.__config[section]:
            self.__config[section][key] = value

    def __check_onnx_file(self):
        """
        Checks if the onnx file exists in the specified path.

        Raises:
        -------
        ValueError
            If the onnx file is not found in the specified path.
        """
        self.__logger.debug("Checking onnx file")
        config_parent_dir = os.path.abspath(
            os.path.dirname(self.__nvinfer_config_file_path))
        if not os.path.exists(os.path.abspath("{}/{}".format(config_parent_dir, self.__onnx_file_path))):
            raise ValueError(
                "Onnx file not found: {}".format(self.__onnx_file_path))

    def __build_engine_file_path(self):
        """
        Builds the file path for the TensorRT engine file based on the batch size and GPU ID.
        """
        engine_file_name = "model_b{}_gpu{}_fp32.engine".format(
            self.__batch_size, self.__gpu_id)
        self.__model_engine_file_path = "{}/{}".format(
            os.getcwd(), engine_file_name)

    def __write_config_file(self):
        """
        Writes the detection configuration to a file.

        The configuration is written to the file path specified in the `__nvinfer_config_file_path` attribute.

        Returns:
            None
        """
        with open(self.__nvinfer_config_file_path, "w") as f:
            self.__config.write(f)
        self.__logger.debug("Wrote detection config to file: {}".format(
            self.__nvinfer_config_file_path))

    def __set_required_fields(self):
        """
            Sets the required fields for object detection.
        """
        # overriding properties

        self.__override_config_field(
            "property", "model-engine-file", self.__model_engine_file_path)

        self.__override_config_field(
            "property", "gpu-id", str(self.__gpu_id))

        self.__override_config_field(
            "property", "batch-size", str(self.__batch_size))

        self.__override_config_field(
            "property", "custom-lib-path", self.__custom_lib_path)

        self.__override_config_field(
            "property", "network-mode", "1")

        self.__override_config_field(
            "property", "process-mode", "1")

        self.__override_config_field(
            "property", "gie-unique-id", "1")

    def __set_optional_fields(self):
        """
            Sets the optional fields for object detection.
        """
        # checking optional fields
        # model-color-format=0
        self.__add_config_field_if_not_exists(
            "property", "model-color-format", "0")

        # net-scale-factor=0.0039215697906911373
        self.__add_config_field_if_not_exists(
            "property", "net-scale-factor", "0.0039215697906911373")

        # label-file-path=labels.txt
        self.__add_config_field_if_not_exists(
            "property", "label-file-path", "labels.txt")

        # num-detected-classes=80
        self.__add_config_field_if_not_exists(
            "property", "num-detected-classes", "80")

        # interval=0
        self.__add_config_field_if_not_exists(
            "property", "interval", "0")

        # gie-unique-id=1
        self.__add_config_field_if_not_exists(
            "property", "gie-unique-id", "1")

        # cluster-mode=2
        self.__add_config_field_if_not_exists(
            "property", "cluster-mode", "2")

        # maintain-aspect-ratio=1
        self.__add_config_field_if_not_exists(
            "property", "maintain-aspect-ratio", "1")

        # symmetric-padding=1
        self.__add_config_field_if_not_exists(
            "property", "symmetric-padding", "1")

        # parse-bbox-func-name=NvDsInferParseYolo
        # #parse-bbox-func-name=NvDsInferParseYoloCuda
        # TODO: cehck if NvDsInferParseYoloCuda can be used
        self.__add_config_field_if_not_exists(
            "property", "parse-bbox-func-name", "NvDsInferParseYolo")

        # engine-create-func-name=NvDsInferYoloCudaEngineGet
        self.__add_config_field_if_not_exists(
            "property", "engine-create-func-name", "NvDsInferYoloCudaEngineGet")

        # nms-iou-threshold=0.45
        self.__add_config_field_if_not_exists(
            "class-attrs-all", "nms-iou-threshold", "0.45")

        # pre-cluster-threshold=0.45
        self.__add_config_field_if_not_exists(
            "class-attrs-all", "pre-cluster-threshold", "0.45")

        # topk=3000
        self.__add_config_field_if_not_exists(
            "class-attrs-all", "topk", "3000")
