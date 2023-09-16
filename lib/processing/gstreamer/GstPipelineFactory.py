from edge.detector.detector_pb2 import RtspStream
from lib.processing.gstreamer.pipelines.GstRtspPipeline import GstRtspPipeline
from lib.processing.gstreamer.pipelines.GstPipeline import GstPipeline
from .elements.outputs import GstPipelineOutput


class GstPipelineFactory(object):
    """description of class"""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(GstPipelineFactory, cls).__new__(cls)
            cls._pipelines: [GstPipeline] = []
        return cls._instance

    def rtsp_detection_factory(self, inputs: [RtspStream], config_file_path=None) -> GstPipeline:
        pipeline = GstRtspPipeline(streams, config_file_path=config_file_path)
        self._instance._pipelines.append(pipeline)
        return pipeline
