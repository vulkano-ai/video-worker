from .GstPipeline import GstPipeline
from lib import Logger
from lib.processing.gstreamer.elements.inputs.GstRtspSrc import GstRtspVideoSrc
from lib.processing.gstreamer.elements.outputs.GstFakeSink import GstFakeSink
from lib.processing.gstreamer.elements.outputs.GstFileOutput import GstFileOutput
from lib.processing.gstreamer.elements.infer.video.DetectionInfer import DetectionInfer
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from edge.detector.detector_pb2 import RtspStream


class GstRtspPipeline(GstPipeline):
    __rtsp_src: GstRtspVideoSrc = None
    __src_video_tee = None
    __video_sink: GstFakeSink = None
    __file_sink: GstFileOutput = None
    __logger = None
    def __init__(self, streams: [RtspStream]):
        super().__init__()
        self.__logger = Logger().get_logger("GstRtspPipeline")
        self.__streams = streams
        self.__num_streams = len(self.__streams)
        self.__elem_id = 0
        self.__streams_info = []

    def _create_rtsp_src(self, uri_id, uri):
        self.__logger.debug("Creating test video source")
        self.__rtsp_src = GstRtspVideoSrc(self._pipeline, elem_id=uri_id, uri=uri)
        self.__rtsp_src.build_source()
        self.__src_video_tee = self.__rtsp_src.get_src_video_tee()
        if self.__src_video_tee is None:
            self.__logger.error("Video tee not found")
            raise Exception("Video tee not found")
        self.__streams_info.append({"uri": uri, "stream_id": uri_id, "tee": self.__src_video_tee})
        self.__logger.debug("Test video source created")

    def _create_video_sink(self, source_id):
        self.__logger.debug("Creating video sink")
        # self.__video_sink = GstFakeSink(self._pipeline, elem_id=source_id, src_video_tee=self.__src_video_tee)
        # self.__video_sink.build_output()

        self.__file_sink = GstFileOutput(self._pipeline,
                                         elem_id=source_id,
                                         video_tee=self.__streams_info[source_id]['tee'],
                                         file_path="./test_%u.mp4" % source_id)
        self.__file_sink.build_output()

        self.__logger.debug("Video sink created")

    def _create_pgie_infer(self):
        self.__logger.debug("Creating PGIE nvinfer")
        src_video_tees = [el["tee"] for el in self.__streams_info]
        self.__pgie = DetectionInfer(pipeline=self._pipeline, elem_id=0, src_video_tees =src_video_tees, streams=self.__streams)
        self.__pgie.build_video_infer()

        for idx, output_tee in enumerate(self.__pgie.get_out_video_tees()):
            self.__streams_info[idx]['tee'] = output_tee

        self.__logger.debug("PGIE nvinfer created")

    def build_pipeline(self):
        self.__logger.debug("Building test pipeline")
        for source_id in range(self.__num_streams):
            self._create_rtsp_src(source_id, self.__streams[source_id].uri)

        self._create_pgie_infer()

        for source_id in range(self.__num_streams):
            self._create_video_sink(source_id)
        self.__logger.debug("Test pipeline successfully built")
