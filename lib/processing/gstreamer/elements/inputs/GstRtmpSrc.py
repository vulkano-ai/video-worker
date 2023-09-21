from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from .GstBaseSrc import GstBaseSrc


class GstRtmpSrc(GstBaseSrc):
    __logger = Logger().get_logger("GstRtmpSrc")
    __location = None
    __rtmp_src = None
    __flvdemux = None
    __video_pad = None
    __audio_pad = None
    __audio_tee = None
    __video_tee = None

    def __init__(self, pipeline, source_id=0, on_video_available=None, on_audio_available=None, location=None):
        super().__init__(
            pipeline=pipeline,
            elem_id=source_id,
            on_video_available=on_video_available,
            on_audio_available=on_audio_available
        )

        self.__location = location
        self.__create_rtmp_src()
        self.__create_flvdemux()
        self.__create_audio_tee()
        self.__create_video_tee()

    def __create_rtmp_src(self):
        self.__logger.debug("Creating rtmp src")
        elem_name = "rtmp-src-%u" % self._source_id
        self.__rtmp_src = make_gst_element("rtmpsrc", elem_name, elem_name)
        self.__rtmp_src.set_property("location", self.__location)
        self.get_pipeline().add(self.__rtmp_src)

    def __create_flvdemux(self):
        self.__logger.debug("Creating flvdemux")
        elem_name = "flvdemux-%u" % self._source_id
        self.__flvdemux = make_gst_element("flvdemux", elem_name, elem_name)
        self.get_pipeline().add(self.__flvdemux)
        self.__flvdemux.connect("pad-added", self.__on_pad_added)
        self.__flvdemux.connect("pad-removed", self.__on_pad_removed)
        self.__flvdemux.connect("no-more-pads", self.__on_no_more_pads)

    def __create_audio_tee(self):
        self.__logger.debug("Creating audio tee")
        elem_name = "rtmp-audio-tee-%u" % self._source_id
        self.__audio_tee = make_gst_element("tee", elem_name, elem_name)
        self.get_pipeline().add(self.__audio_tee)

    def __create_video_tee(self):
        self.__logger.debug("Creating video tee")
        elem_name = "rtmp-video-tee-%u" % self._source_id
        self.__video_tee = make_gst_element("tee", elem_name, elem_name)
        self.get_pipeline().add(self.__video_tee)

    def __on_pad_added(self, element, pad):
        self.__logger.debug("Pad added")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))

        if name.startswith("audio"):
            self.__logger.debug("Audio pad added")
            self.__audio_pad = pad

        elif name.startswith("video"):
            self.__logger.debug("Video pad added")
            self.__video_pad = pad
        else:
            self.__logger.debug("Unknown pad added")

    def __on_pad_removed(self, element, pad):
        self.__logger.debug("Pad removed")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        if name.startswith("audio"):
            self.__logger.debug("Audio pad removed")
        elif name.startswith("video"):
            self.__logger.debug("Video pad removed")
        else:
            self.__logger.debug("Unknown pad removed")
        # TODO: Implement pad removal

    def __on_no_more_pads(self, element):
        self.__logger.debug("No more pads")
        self.__logger.debug("Building source")
        self._on_audio_available(self.__audio_tee)
        self._on_video_available(self.__video_pad)

    def build_source(self):
        self.__logger.debug("Video source built")
        self.__rtmp_src.link(self.__flvdemux)
