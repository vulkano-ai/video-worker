from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from .GstBaseSink import GstBaseSink

"""
gst-launch-1.0 videotestsrc ! nvvideoconvert ! 'video/x-raw(memory:NVMM), width=640, height=480, framerate=30/1, format=NV12' \
 ! nvv4l2h264enc ! video/x-h264 ! h264parse ! video/x-h264, stream-format=avc ! h264parse ! video/x-h264 !  qtmux ! filesink location=test.mp4 
"""


class GstFileOutput(GstBaseSink):
    __logger = None
    __pipeline = None
    __video_tee = None
    __file_path = None

    __encoder = None
    __encoder_caps = None
    __parser = None
    __parser_caps = None
    __file_sink = None

    __queue = None

    def __init__(self, pipeline, elem_id, video_tee, file_path):
        super().__init__(pipeline, elem_id, video_tee, None)
        self.__logger = Logger().get_logger("GstFileOutput")

        self.__logger.debug("Creating file output")
        self.__file_path = file_path

    def __create_queue(self):
        self.__logger.debug("Creating queue")
        self.__queue = make_gst_element("queue", "queue-file_%u"%self._elem_id, "queue-file_%u"%self._elem_id)
        self._pipeline.add(self.__queue)
        self.__logger.debug("Queue created")


    def __create_encode(self):
        self.__logger.debug("Creating encode")
        self.__encode = make_gst_element("nvv4l2h264enc", "nvv4l2h264enc_%u"%self._elem_id, "nvv4l2h264enc_%u"%self._elem_id)
        # self.__encode.set_property("bitrate", 4000000)
        self._pipeline.add(self.__encode)
        self.__logger.debug("Encode created")

    def __create_parse(self):
        self.__logger.debug("Creating parse")
        self.__parse = make_gst_element("h264parse", "h264parse_output_%u"%self._elem_id, "h264parse_output_%u"%self._elem_id)
        self._pipeline.add(self.__parse)
        self.__logger.debug("Parse created")

    def __create_mux(self):
        self.__logger.debug("Creating mux")
        self.__mux = make_gst_element("matroskamux", "matroskamux_%u"%self._elem_id, "matroskamux_%u"%self._elem_id)
        self._pipeline.add(self.__mux)
        self.__logger.debug("Mux created")

    def __create_file_sink(self):
        self.__logger.debug("Creating file sink")
        self.__file_sink = make_gst_element("filesink", "filesink_%u"%self._elem_id, "filesink_%u"%self._elem_id)
        self.__file_sink.set_property("location", self.__file_path)
        self._pipeline.add(self.__file_sink)
        self.__logger.debug("File sink created")

    def build_output(self):
        self.__create_queue()
        self.__create_encode()
        self.__create_parse()
        self.__create_mux()
        self.__create_file_sink()

        self._src_video_tee.link(self.__queue)
        self.__queue.link(self.__encode)
        self.__encode.link(self.__parse)

        video_src_pad = self.__parse.get_static_pad("src")
        video_sink_pad = self.__mux.get_request_pad("video_0")
        video_src_pad.link(video_sink_pad)

        # self.__parse.link(self.__mux)

        self.__mux.link(self.__file_sink)

        self.__logger.debug("File output built")
