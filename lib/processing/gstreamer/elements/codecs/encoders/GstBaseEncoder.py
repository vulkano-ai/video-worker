from lib import Logger
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement



class GstBaseEncoder(GstBaseElement):
    __logger = None
    __name = None

    def __init__(self, pipeline, elem_id=0, name=None):
        super().__init__(pipeline=pipeline, elem_id=elem_id)
        self.__logger = Logger().get_logger("GstBaseEncoder")

        self.__logger.debug("Creating Base Encoder")
        self.__name = name
        self.__logger.debug("Base Encoder element created")

    def get_encoder_name(self):
        return self.__name
