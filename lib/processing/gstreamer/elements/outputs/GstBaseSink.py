from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from abc import abstractmethod
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement


class GstBaseSink(GstBaseElement):
    __logger = None
    _src_video_tee = None
    _src_audio_tee = None

    def __init__(self, pipeline, elem_id, src_video_tee, src_audio_tee):
        super().__init__(pipeline=pipeline, elem_id=elem_id)
        self.__logger = Logger().get_logger("GstBaseSink")

        self.__logger.debug("Creating Base sink element")
        self._src_video_tee = src_video_tee
        self._src_audio_tee = src_audio_tee
        self.__logger.debug("Base sink element created")

    @abstractmethod
    def build_output(self):
        pass
