from lib.processing.gstreamer.GstPipelineRunner import GstPipelineRunner
from inference.pipeline.pipeline_pb2 import Pipeline, PipelineInput, PipelineOutput
from lib.processing.gstreamer.elements.inputs.GstRtmpSrc import GstRtmpSrc
from lib.common.Logger import Logger


class GstPipeline(GstPipelineRunner):
    """description of class"""
    __logger = None
    __source = None

    def __init__(self):
        super().__init__(
            error_callback=self.__on_error,
            eos_callback=self.__on_eos,
            state_change_callback=self.__on_state_change
        )
        self.__logger = Logger().get_logger("GstPipeline")

    def __on_error(self, bus, message):
        pass

    def __on_eos(self, bus, message):
        pass

    def __on_state_change(self, bus, message):
        pass

    def create_livestream_pipeline(self, pipeline: Pipeline):
        self.__gst_pipeline = GstPipeline(
            error_callback=self.__on_error,
            eos_callback=self.__on_eos,
            state_change_callback=self.__on_state_change
        )
        self._create_input_source(pipeline)

        pass

    def _create_input_source(self, pipeline: Pipeline):
        inputs = pipeline.input

        if pipeline.input.source.type == Pipeline.Input.Source.RTMP:
            self.__source = GstRtmpSrc(
                pipeline=pipeline,
                on_audio_available=self._create_audio_decoder,
                on_video_available=self._create_video_decoder,
                location=pipeline.input.source.location
            )
        pass

    def _create_video_decoder(self, pad):
        self.__logger.debug("Creating video decoder")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        # DecoderFactory.create_decoder(pad)
        pass

    def _create_audio_encoder(self, pad):
        pass

    def _create_video_encoder(self, pipeline: Pipeline):
        pass

    def _create_audio_decoder(self, pipeline: Pipeline):
        pass

    def _create_output_sink(self, pipeline: Pipeline):
        pass
