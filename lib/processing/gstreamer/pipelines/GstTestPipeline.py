from .GstPipeline import GstPipeline
from lib import Logger
from lib.processing.gstreamer.elements.inputs.GstVideoTestSrc import GstVideoTestSrc
from lib.processing.gstreamer.elements.outputs.GstFakeSink import GstFakeSink
from lib.processing.gstreamer.elements.outputs.GstFileOutput import GstFileOutput
from lib.processing.gstreamer.utils.gst_utils import make_gst_element


class GstTestPipeline(GstPipeline):
    __video_src: GstVideoTestSrc = None
    __src_video_tee = None
    __fake_sink: GstFakeSink = None
    __file_sink: GstFileOutput = None
    __logger = Logger().get_logger("GstTestPipeline")

    def __init__(self):
        super().__init__()

    def _create_test_video_src(self):
        self.__logger.debug("Creating test video source")
        self.__video_src = GstVideoTestSrc(self._pipeline)
        self.__video_src.build_source()
        self.__src_video_tee = self.__video_src.get_src_video_tee()

    def _create_video_sink(self):
        self.__logger.debug("Creating video sink")

        # self.__fake_sink = GstFakeSink(self._pipeline, self.__src_video_tee)
        self.__file_sink = GstFileOutput(self._pipeline, self.__src_video_tee, "./test.mov")

        # self.__fake_sink.build_output()
        self.__file_sink.build_output()

        self.__logger.debug("Video sink created")

    def build_pipeline(self):
        self.__logger.debug("Building test pipeline")
        self._create_test_video_src()
        self._create_video_sink()
        self.__logger.debug("Test pipeline successfully built")
