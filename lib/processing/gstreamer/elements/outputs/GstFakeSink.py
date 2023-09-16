from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from .GstBaseSink import GstBaseSink


class GstFakeSink(GstBaseSink):
    __logger = None
    __fake_sink = None
    __queue = None

    def __init__(self, pipeline, elem_id=0, src_video_tee=None, src_audio_tee=None):
        super().__init__(pipeline=pipeline, elem_id=elem_id, src_video_tee=src_video_tee, src_audio_tee=src_audio_tee)
        self.__logger = Logger().get_logger("GstFakeSink")

        self.__logger.debug("Creating fake output")

    def __create_fake_sink(self):
        self.__logger.debug("Creating fake sink")
        self.__fake_sink = make_gst_element("fakesink", "fakesink_%u"%self._elem_id, "fakesink_%u"%self._elem_id)
        self._pipeline.add(self.__fake_sink)
        self.__logger.debug("Fake sink created")

    def __create_queue(self):
        self.__logger.debug("Creating queue")
        self.__queue = make_gst_element("queue", "queue-fake_%u"%self._elem_id, "queue-fake_%u"%self._elem_id)
        self._pipeline.add(self.__queue)
        self.__logger.debug("Queue created")

    def build_output(self):
        self.__create_queue()
        self.__create_fake_sink()
        if self._src_video_tee is None:
            self.__logger.error("Video tee is None")
            return

        src_pad = self._src_video_tee.get_request_pad("src_%u")
        queue_sink_pad = self.__queue.get_static_pad("sink")
        src_pad.link(queue_sink_pad)

        self._src_video_tee.link(self.__queue)
        self.__queue.link(self.__fake_sink)
        self.__logger.debug("Fake output built")
