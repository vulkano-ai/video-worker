from lib import Logger
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement


class GstBaseDecoder(GstBaseElement):
    """
    Base class for GStreamer decoders.

    Args:
        pipeline (GstPipeline): The GStreamer pipeline.
        elem_id (int): The ID of the element.
        name (str): The name of the decoder.

    Attributes:
        __logger (Logger): The logger instance.
        __name (str): The name of the decoder.
    """

    __logger = None
    __name = None

    def __init__(self, pipeline, elem_id=0, name=None):
        super().__init__(pipeline=pipeline, elem_id=elem_id)
        self.__logger = Logger().get_logger("GstBaseDecoder")

        self.__logger.debug("Creating Base Decoder")
        self.__name = name
        self.__logger.debug("Base Decoder element created")

    def get_decoder_name(self):
        """
        Returns the name of the decoder.

        Returns:
            str: The name of the decoder.
        """
        return self.__name
