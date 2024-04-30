from lib.common.Logger import Logger
from .GstRtmpSrc import GstRtmpSrc
from inference.pipeline.pipeline_pb2 import Pipeline, PipelineInput, InputProtocol, OutputProtocol, InputProvider, OutputProvider
from inference.providers.providers_pb2 import RtmpProviderConfig, HlsProviderConfig
from gi.repository import Gst


class GstInputFactory(object):
    """
    A factory class for creating input sources for Gstreamer pipelines.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GstInputFactory, cls).__new__(cls)
            cls._instance.__logger = Logger().get_logger("GstInputFactory")
            cls._instance.__logger.debug("Creating GstInputFactory")
        return cls._instance

    def create_input_source(
        self,
        input: PipelineInput = None,
        elem_id: int = None,
        gst_pipeline: Gst.Pipeline = None,
        on_video_available: callable = None,
        on_audio_available: callable = None
    ):
        """
        Creates an input source for a Gstreamer pipeline.

        Args:
            input (PipelineInput): The input configuration.
            elem_id (int): The ID of the Gstreamer element.
            gst_pipeline (Gst.Pipeline): The Gstreamer pipeline.
            on_video_available (callable): A callback function to be called when video is available.
            on_audio_available (callable): A callback function to be called when audio is available.

        Returns:
            GstRtmpSrc: The input source.
        """
        assert input is not None, "Input must be set"
        assert elem_id is not None, "Element id must be set"
        assert gst_pipeline is not None, "Gstreamer pipeline must be set"
        assert on_video_available is not None or on_audio_available is not None, "At least one callback must be provided"

        return self.__handle_input(
            input=input,
            elem_id=elem_id,
            gst_pipeline=gst_pipeline,
            on_video_available=on_video_available,
            on_audio_available=on_audio_available
        )

    def __handle_input(self, input: PipelineInput, elem_id, gst_pipeline, on_video_available: callable, on_audio_available: callable):
        """
        Handles the creation of an input source for a Gstreamer pipeline.

        Args:
            input (PipelineInput): The input configuration.
            elem_id (int): The ID of the Gstreamer element.
            gst_pipeline (Gst.Pipeline): The Gstreamer pipeline.
            on_video_available (callable): A callback function to be called when video is available.
            on_audio_available (callable): A callback function to be called when audio is available.

        Returns:
            GstRtmpSrc: The input source.
        """
        self._instance.__logger.debug("Handling input")
        if input.protocol == InputProtocol.INPUT_RTMP:
            return self.__create_internal_rtmp_input(
                input=input,
                elem_id=elem_id,
                gst_pipeline=gst_pipeline,
                on_video_available=on_video_available,
                on_audio_available=on_audio_available
            )
        return None

    def __create_internal_rtmp_input(self, input: PipelineInput, elem_id, gst_pipeline, on_video_available: callable, on_audio_available: callable):
        """
        Creates an internal RTMP input source for a Gstreamer pipeline.

        Args:
            input (PipelineInput): The input configuration.
            elem_id (int): The ID of the Gstreamer element.
            gst_pipeline (Gst.Pipeline): The Gstreamer pipeline.
            on_video_available (callable): A callback function to be called when video is available.
            on_audio_available (callable): A callback function to be called when audio is available.

        Returns:
            GstRtmpSrc: The input source.
        """
        self.__logger.debug("Creating internal rtmp source")
        config = input.rtmpConfig
        assert config is not None, "Rtmp config must be set"
        assert config.uri is not None, "Rtmp uri must be set"
        rtmp_src = GstRtmpSrc(
            pipeline=gst_pipeline,
            elem_id=elem_id,
            on_audio_available=on_audio_available,
            on_video_available=on_video_available,
            location=config.uri
        )
        return rtmp_src
