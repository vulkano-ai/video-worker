from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from abc import abstractmethod
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement

class GstBaseVideoInfer(GstBaseElement):
    __logger = None
    _src_video_tees = []
    _out_video_tees = []

    def __init__(self, pipeline, elem_id, src_video_tees):
        super().__init__(pipeline=pipeline, elem_id=elem_id)
        self.__logger = Logger().get_logger("GstBaseVideoInfer")

        self.__logger.debug("Creating Base video infer element")
        self._src_video_tees = src_video_tees

        for idx in range(len(src_video_tees)):
            self._create_out_tee(idx)
        self.__logger.debug("Base video infer element created")

    def _create_out_tee(self, idx):
        tee_out = make_gst_element("tee", "tee_pgie_video_out_%u" % idx, "tee_pgie_video_out_%u" % idx)

        self._pipeline.add(tee_out)
        self._out_video_tees.append(tee_out)

    def get_out_video_tees(self):
        return self._out_video_tees

    @abstractmethod
    def build_video_infer(self):
        pass