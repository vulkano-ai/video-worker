from common import Logger
from .video import GstAvDecoder, GstNvv4lDecoder, GstVaapiDecoder
from lib.processing.gstreamer import utils as gst_utils


class GstVideoDecoderFactory(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GstVideoDecoderFactory, cls).__new__(cls)
            cls._instance.__logger = Logger().get_logger("GstVideoDecoderFactory")
            cls._instance.__logger.debug("Creating GstVideoDecoderFactory")

    def create_video_decoder(self, pad):
        self.__logger.debug("Creating video decoder")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        # extract media type
        media_type = caps.get_structure(0).get_name()
        self.__logger.debug("Media type: {}".format(media_type))
        pass
