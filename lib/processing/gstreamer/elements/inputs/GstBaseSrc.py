from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from abc import abstractmethod
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement


class GstBaseSrc(GstBaseElement):
    __logger = None
    _src_video_tee = None
    _src_audio_tee = None

    def __init__(self, pipeline, elem_id=0):
        super().__init__(pipeline, elem_id)
        self.__logger = Logger().get_logger("GstBaseSrc")
        self.__create_src_video_tee()
        self.__create_src_audio_tee()

    def __create_src_video_tee(self):
        elem_name = "src-video-tee-%u" % self._elem_id
        self.__logger.debug("Creating video tee {} for source {}".format(elem_name, self._elem_id))
        self._src_video_tee = make_gst_element("tee", elem_name, elem_name)
        self._pipeline.add(self._src_video_tee)
        self.__logger.debug("Video tee {} created for source {}".format(elem_name, self._elem_id))

    def __create_src_audio_tee(self):
        elem_name = "src-audio-tee-%u" % self._elem_id
        self.__logger.debug("Creating audio tee {} for source {}".format(elem_name, self._elem_id))
        self._src_audio_tee = make_gst_element("tee", elem_name, elem_name)
        self._pipeline.add(self._src_audio_tee)
        self.__logger.debug("Audio tee {} created for source {}".format(elem_name, self._elem_id))

    def get_src_video_tee(self):
        return self._src_video_tee

    def get_src_audio_tee(self):
        return self._src_audio_tee

    @abstractmethod
    def build_source(self):
        pass
