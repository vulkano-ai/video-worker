from lib import Logger
from lib.processing.gstreamer.elements.codecs.decoders.GstBaseDecoder import GstBaseDecoder, VideoEncodings, GstDecoderClass
from lib.processing.gstreamer.utils.gst_utils import make_gst_element


# TODO: Add support for more encodings
class GstAvDecoder(GstBaseDecoder):

    __logger = None
    __parser = None
    __decoder = None
    __supported_encodings = [
        VideoEncodings.H264,
        VideoEncodings.H265
    ]
    __decoder_class = GstDecoderClass.AVDECODER

    def __init__(self, pipeline, elem_id=0):
        super().__init__(
            pipeline=pipeline,
            elem_id=elem_id,
            name="AVDecoder",
            decoder_class=self.__decoder_class,
            supported_encodings=self.__supported_encodings
        )
        self.__logger = Logger().get_logger("AVDecoder")

        self.__logger.debug("AV Decoder element created")

    def init_decoder(self, mdia_type):
        """
        Initializes the decoder.
        """
        self.__logger.debug("Initializing AV Decoder")
        self.__create_parser()
        self.__create_decoder()
        self.__logger.debug("AV Decoder initialized")

    def __create_parser(self):
        """
        Creates a H264 parser element and adds it to the pipeline.
        """
        self.__logger.debug("Creating H264 Parser")

        self.__parser = make_gst_element(
            "h264parse", "h264_parser-%u" % self._elem_id, "h264_parser")
        self.pipeline.add(self.__parser)

        self.__logger.debug("H264 Parser created")

    def __create__h264_decoder(self):
        """
        Creates a H264 depayloader element and adds it to the pipeline.
        """
        self.__logger.debug("Creating H264 Depay")

        self.__decoder = make_gst_element(
            "avdec_h264", "avdec_h264-%u" % self._elem_id, "avdec_h264")
        self.pipeline.add(self.__depay)

        self.__logger.debug("H264 Depay created")

    def __create__h265_decoder(self):
        """
        Creates a H265 depayloader element and adds it to the pipeline.
        """
        self.__logger.debug("Creating H265 Depay")

        self.__decoder = make_gst_element(
            "avdec_h265", "avdec_h265-%u" % self._elem_id, "avdec_h265")
        self.pipeline.add(self.__depay)

        self.__logger.debug("H265 Depay created")

    @property
    def parser(self):
        """
        Returns the H264 parser element.

        Returns:
        Gst.Element: The H264 parser element.
        """
        return self.__parser

    @property
    def decoder(self):
        """
        Returns the H264 decoder element.

        Returns:
        Gst.Element: The H264 decoder element.
        """
        return self.__decoder

    def on_video_available(self, pad):
        """
        A callback method that is called when a video pad is available.

        Args:
        pad (Gst.Pad): The video pad that is available.
        """

        self.__logger.debug("Video pad available")

        self.__logger.debug("Linking parser to depay")
        self.__parser.link(self.__depay)

        self.__logger.debug("Linking depay to video pad")
        self.__depay.link(pad)
