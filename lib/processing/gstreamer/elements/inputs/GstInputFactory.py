from common import Logger
from . import GstRtmpSrc
from inference.pipeline.pipeline_pb2 import Pipeline, PipelineInput, InputProtocol, OutputProtocol, InputProvider, OutputProvider
from inference.providers.providers_pb2 import RtmpProviderConfig, HlsProviderConfig


class GstInputFactoryFactory(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GstInputFactoryFactory, cls).__new__(cls)
            cls._instance.__logger = Logger().get_logger("GstInputFactoryFactory")
            cls._instance.__logger.debug("Creating GstInputFactoryFactory")

    def create_input_source(self, input: PipelineInput, elem_id, gst_pipeline, on_video_available: callable, on_audio_available: callable):
        assert input is not None, "Input must be set"
        assert elem_id is not None, "Element id must be set"
        assert gst_pipeline is not None, "Gstreamer pipeline must be set"
        assert on_video_available is not None or on_audio_available is not None, "At least one callback must be provided"

        if input.protocol == InputProtocol.RTMP and input.providerType == InputProvider.INPUT_INTERNAL:
            return self.__create_internal_rtmp_input(
                    input=input,
                    elem_id=elem_id,
                    gst_pipeline=gst_pipeline, 
                    on_video_available=on_video_available,
                    on_audio_available=on_audio_available
                )
        
        return None


    def __create_internal_rtmp_input(self, input: PipelineInput, elem_id, gst_pipeline, on_video_available: callable, on_audio_available: callable):
        self.__logger.debug("Creating internal rtmp source")
        config = input.config.rtmpConfig
        assert config is not None, "Rtmp config must be set"
        assert config.uri is not None, "Rtmp uri must be set"
        rtmp_src = GstRtmpSrc(
            pipeline=gst_pipeline,
            elem_id=elem_id,
            on_audio_available=on_audio_available,
            on_video_available=on_video_available,
            location=config.uri
        )
        # TODO: save rtmp_src to a list and return it?
        return rtmp_src