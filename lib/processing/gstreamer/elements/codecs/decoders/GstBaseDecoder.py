from lib import Logger
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement
from abc import abstractmethod


class GstDecoderClass(object):
    VAAPI = "vaapi"  # Video Acceleration API
    NVV4L2 = "nvv4l2decoder"  # NVIDIA Video 4 Linux 2
    AVDECODER = "avdec"  # Libav decoder


class VideoEncodings(object):
    H264 = "video/x-h264"
    H265 = "video/x-h265"
    VP8 = "video/x-vp8"
    VP9 = "video/x-vp9"
    JPEG = "image/jpeg"
    AV1 = "AV1"

    # MJPEG = "image/mjpeg"
    # MPEG2 = "MPEG2"
    # MPEG4 = "MPEG4"


class GstBaseDecoder(GstBaseElement):
    """
    Base class for GStreamer decoders.

    Args:
        pipeline (GstPipeline): The GStreamer pipeline.
        elem_id (int): The ID of the element.
        decoder_class (GstDecoderClass): The decoder class.
        supported_encodings ([VideoEncodings]): The supported encodings.

    Attributes:
        __logger (Logger): The logger instance.
        __decoder_class (GstDecoderClass): The decoder class.
        __supported_encodings ([VideoEncodings]): The supported encodings.
    """

    __logger = None
    __decoder_class = None
    __supported_encodings = None

    def __init__(self, pipeline, elem_id=0, decoder_class: GstDecoderClass = None, supported_encodings: [VideoEncodings] = None):
        super().__init__(pipeline=pipeline, elem_id=elem_id)
        self.__logger = Logger().get_logger("GstBaseDecoder")

        self.__logger.debug("Creating Base Decoder")
        self.__decoder_class = decoder_class
        self.__supported_encodings = supported_encodings
        self.__logger.debug("Base Decoder element created")

    @abstractmethod
    def init_decoder(self):
        """
        Initializes the decoder.
        """
        pass

    @abstractmethod
    def is_available(self, media_type):
        pass

    @property
    def name(self):
        """
        Returns the name of the decoder.

        Returns:
            str: The name of the decoder.
        """
        return self.__name

    @property
    def decoder_class(self):
        """
        Returns the decoder class.

        Returns:
            GstDecoderClass: The decoder class.
        """
        return self.__decoder_class

    @property
    def supported_encodings(self):
        """
        Returns the supported encodings.

        Returns:
            [VideoEncodings]: The supported encodings.
        """
        return self.__supported_encodings

    def is_supported_encoding(self, encoding: VideoEncodings):
        """
        Checks if the given encoding is supported by the decoder.

        Args:
            encoding (VideoEncodings): The encoding to check.

        Returns:
            bool: True if the encoding is supported, False otherwise.
        """
        return encoding in self.__supported_encodings
