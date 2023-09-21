from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from .GstBaseSrc import GstBaseSrc


class GstVideoTestSrc(GstBaseSrc):
    __logger = Logger().get_logger("GstTestVideoSrc")
    _video_src = None
    _src_caps_filter = None
    _video_parse = None
    _convert_caps_filter = None

    def __init__(self, pipeline, source_id=0):
        super().__init__(pipeline=pipeline, elem_id=source_id)
        self._create_video_src()
        self._create_src_caps_filter()
        self._create_convert()

    def _create_video_src(self):
        elem_name = "videotestsrc-%u" % self._source_id
        self.__logger.debug("Creating video source")
        self._video_src = make_gst_element(
            "videotestsrc", elem_name, elem_name)
        self._video_src.set_property("pattern", "ball")
        self.get_pipeline().add(self._video_src)
        self.__logger.debug("Video source {} created for source {}".format(
            elem_name, self._source_id))

    def _create_src_caps_filter(self):
        self.__logger.debug("Creating src caps filter")
        elem_name = "src-caps-filter-%u" % self._source_id
        self._src_caps_filter = make_gst_element(
            "capsfilter", elem_name, elem_name)
        self._src_caps_filter.set_property("caps", Gst.Caps.from_string(
            "video/x-raw, width=640, height=480, framerate=30/1, format=I420"))
        self.get_pipeline().add(self._src_caps_filter)
        self.__logger.debug("Src caps filter created")

    def _create_convert(self):
        self.__logger.debug("Creating convert")
        elem_name = "src-convert-%u" % self._source_id
        self._video_parse = make_gst_element(
            "nvvideoconvert", elem_name, elem_name)
        self.get_pipeline().add(self._video_parse)
        self.__logger.debug("Convert created")

    def build_source(self):
        self._video_src.link(self._src_caps_filter)
        self._src_caps_filter.link(self._video_parse)
        self._video_parse.link(self._src_video_tee)
        self.__logger.debug("Video source built")
