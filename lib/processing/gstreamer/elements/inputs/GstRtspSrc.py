from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from .GstBaseSrc import GstBaseSrc


class GstRtspVideoSrc(GstBaseSrc):
    __logger = None
    __uri = None
    __rtsp_src = None
    __depay = None
    __parse = None
    __decode = None
    __convert = None
    __caps_filter = None
    __framerate = None
    __rtsp_stream_encoding = None
    __width = None
    __height = None

    def __init__(self, pipeline, elem_id=0, uri=None):
        super().__init__(pipeline, elem_id)
        self.__logger = Logger().get_logger("GstRtspSrc")
        self.__uri = uri
        self.__elem_id = elem_id
        self.__logger.debug("Creating RTSP source")
        self.__create_depay()
        self.__create_rtsp_src()
        self.__create_parse()
        self.__create_decode()

    def __create_rtsp_src(self):
        self.__logger.debug("Creating video source")
        self.__rtsp_src = make_gst_element("rtspsrc", "rtspsrc_%u"%self.__elem_id, "rtspsrc_%u"%self.__elem_id)
        self.__rtsp_src.set_property("location", self.__uri)
        self.__rtsp_src.set_property("latency", 0)
        self._pipeline.add(self.__rtsp_src)
        self.__logger.debug("Video source created")

    def __create_depay(self):
        self.__logger.debug("Creating depay")
        self.__depay = make_gst_element("rtph264depay", "rtph264depay_%u"%self.__elem_id, "rtph264depay_%u"%self.__elem_id)
        self._pipeline.add(self.__depay)
        self.__logger.debug("Depay created")

    def __create_parse(self):
        self.__logger.debug("Creating parse")
        elem_name = "h264parse_source_%u" % self.__elem_id
        self.__parse = make_gst_element("h264parse", elem_name, elem_name)
        self._pipeline.add(self.__parse)
        self.__logger.debug("Parse created")

    def __create_decode(self):
        self.__logger.debug("Creating decode")
        self.__decode = make_gst_element("nvv4l2decoder", "nvv4l2decoder_%u"%self.__elem_id, "nvv4l2decoder_%u"%self.__elem_id)
        self._pipeline.add(self.__decode)
        self.__logger.debug("Decode created")

    def __on_pad_added(self, element, pad, depay):
        self.__logger.debug("Dynamic pad created, linking source/depay")
        encoding = pad.get_current_caps().get_structure(0).get_value("encoding-name")
        if encoding == "H264":
            self.__logger.info("Found H264 pad, linking to depay")
            depay_sink_pad = depay.get_static_pad('sink')
            pad.link(depay_sink_pad)

    def __on_pad_removed(self, element, pad):
        '''Unlinks the rtspsrc element from the depayer'''
        self.__logger.debug('Pad removed from rtspsrc element.')
        depaySinkPad = self.__depay.get_static_pad('sink')
        pad.unlink(depaySinkPad)

    def __on_sdp(self, element, sdp, depay):
        self.__logger.debug("SDP received, extracting video info")
        # print sdp media info
        self.__logger.debug("SDP:\n%s" % sdp.medias_len())
        for i in range(sdp.medias_len()):
            media = sdp.get_media(i)
            if media.get_media() == "video":
                self.__extract_video_info(media)

    def __extract_video_info(self, media):
        self.__logger.debug("Extracting video info")
        self.__framerate = media.get_attribute_val("framerate")
        self.__rtsp_stream_encoding = media.get_attribute_val("rtpmap").split()[1].split("/")[0]
        resolution = media.get_attribute_val("framesize").split()[1]
        self.__width = resolution.split("-")[0]
        self.__height = resolution.split("-")[1]
        self.__logger.debug("Video info extracted, framerate: %s, encoding: %s, resolution: %sx%s" % (
            self.__framerate, self.__rtsp_stream_encoding, self.__width, self.__height))

    def get_width(self):
        return self.__width

    def get_height(self):
        return self.__height

    def get_framerate(self):
        return self.__framerate

    def get_encoding(self):
        return self.__rtsp_stream_encoding

    def build_source(self):

        self.__depay.link(self.__parse)
        self.__parse.link(self.__decode)
        self.__decode.link(self._src_video_tee)

        if self.__depay is None:
            raise Exception("Depay not created")

        self.__rtsp_src.connect("pad-added", self.__on_pad_added, self.__depay)
        self.__rtsp_src.connect("on-sdp", self.__on_sdp, self.__depay)

        self.__logger.debug("Video source built")

