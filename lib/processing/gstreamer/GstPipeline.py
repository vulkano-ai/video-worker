from lib.processing.gstreamer.GstPipelineRunner import GstPipelineRunner
from lib.processing.gstreamer.elements.inputs.GstInputFactory import GstInputFactory
from lib.common.Logger import Logger
from inference.pipeline.pipeline_pb2 import StartPipelineRequest, Pipeline, PipelineInput, PipelineOutput, InputProtocol, OutputProtocol, InputProvider, OutputProvider
from inference.providers.providers_pb2 import RtmpProviderConfig, HlsProviderConfig


class GstPipeline(GstPipelineRunner):
    """description of class"""
    __logger = None
    __sources = []
    __pipeline_request = None

    def __init__(self):
        super().__init__(
            error_callback=self.__on_error,
            eos_callback=self.__on_eos,
            state_change_callback=self.__on_state_change
        )
        self.__logger = Logger().get_logger("GstPipeline")

    def __on_error(self, bus, message):
        self.__logger.error("Error from element {}: {}".format(
            message.src.get_name(), message.parse_error()))
        self.stop_pipeline()
        pass

    def __on_eos(self, bus, message):
        self.__logger.error("EOS from element {}: {}".format(
            message.src.get_name(), message.parse_error()))
        self.stop_pipeline()
        pass

    def __on_state_change(self, bus, message):
        pass

    def create_livestream_pipeline(self, pipeline_request: StartPipelineRequest):
        self.__pipeline_request = pipeline_request

        self.__logger.debug("Creating input source")
        self.__create_input_source(pipeline_request.pipeline)
        self.set_playing()
        pass

    def __create_input_source(self, pipeline: Pipeline):
        inputs = pipeline.inputs
        assert inputs, "Pipeline must have at least one input"

        for elem_id, input in enumerate(inputs):
            source = GstInputFactory().create_input_source(
                input=input,
                elem_id=elem_id,
                gst_pipeline=self.gst_pipeline,
                on_video_available=self.__create_video_decoder,
                on_audio_available=self.__create_audio_encoder
            )
            if source is None:
                raise Exception("Unsupported input type")

            source.create()
            source.add_to_pipeline()
            source.link()
            self.__sources.append(source)

        self.__logger.debug(f"Created {len(self.__sources)} input sources")

    def __create_video_decoder(self, pad):
        self.__logger.debug("Creating video decoder")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        # DecoderFactory.create_decoder(pad)
        pass

    def __create_audio_encoder(self, pad):
        pass

    def _create_video_encoder(self, pipeline: Pipeline):
        pass

    def _create_audio_decoder(self, pipeline: Pipeline):
        pass

    def _create_output_sink(self, pipeline: Pipeline):
        pass
