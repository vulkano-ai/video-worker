from lib import Logger
from lib.processing.gstreamer.elements.codecs.decoders.GstBaseDecoder import GstBaseDecoder
from lib.processing.gstreamer.utils.gst_utils import make_gst_element


class GstH264VideoDecoder(GstBaseDecoder):
    """
    A class representing a H264 video decoder element in GStreamer.

    Attributes:
    __logger (Logger): A logger object for logging debug messages.
    __parser (Gst.Element): A GStreamer element for parsing H264 video streams.
    __depay (Gst.Element): A GStreamer element for depayloading RTP packets containing H264 video streams.

    Methods:
    __init__(self, pipeline, elem_id=0): Initializes a GstH264VideoDecoder object.
    __create_parser(self): Creates a H264 parser element and adds it to the pipeline.
    __create_depay(self): Creates a H264 depayloader element and adds it to the pipeline.
    parser: A property that returns the H264 parser element.
    depay: A property that returns the H264 depayloader element.
    """

    __logger = None
    __parser = None
    __depay = None

    def __init__(self, pipeline, elem_id=0):
        """
        Initializes a GstH264VideoDecoder object.

        Args:
        pipeline (Gst.Pipeline): The GStreamer pipeline to which the decoder element will be added.
        elem_id (int): An optional integer ID for the decoder element. Defaults to 0.
        """
        super().__init__(pipeline=pipeline, elem_id=elem_id, name="h264")
        self.__logger = Logger().get_logger("H264Decoder")

        self.__logger.debug("Creating H264 Decoder")

        self.__create_parser()
        self.__create_depay()

        self.__logger.debug("H264 Decoder element created")

    def __create_parser(self):
        """
        Creates a H264 parser element and adds it to the pipeline.
        """
        self.__logger.debug("Creating H264 Parser")

        self.__parser = make_gst_element(
            "h264parse", "h264_parser-%u" % self._elem_id, "h264_parser")
        self.get_pipeline().add(self.__parser)

        self.__logger.debug("H264 Parser created")

    def __create_depay(self):
        """
        Creates a H264 depayloader element and adds it to the pipeline.
        """
        self.__logger.debug("Creating H264 Depay")

        self.__depay = make_gst_element(
            "rtph264depay", "h264_depay-%u" % self._elem_id, "h264_depay")
        self.get_pipeline().add(self.__depay)

        self.__logger.debug("H264 Depay created")

    @property
    def parser(self):
        """
        Returns the H264 parser element.

        Returns:
        Gst.Element: The H264 parser element.
        """
        return self.__parser

    @property
    def depay(self):
        """
        Returns the H264 depayloader element.

        Returns:
        Gst.Element: The H264 depayloader element.
        """
        return self.__depay

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
