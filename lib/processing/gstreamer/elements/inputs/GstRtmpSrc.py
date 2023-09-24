from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from .GstBaseSrc import GstBaseSrc


class GstRtmpSrc(GstBaseSrc):
    __logger = Logger().get_logger("GstRtmpSrc")
    __location = None
    __rtmp_src = None
    __flvdemux = None
    __audio_tee = None
    __video_tee = None
    __audio_pad = None
    __video_pad = None
    __output_audio_pads = []
    __output_video_pads = []

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

    def __del__(self):
        self.__logger.debug("Deleting rtmp src")
        self.__rtmp_src.set_state(Gst.State.NULL)
        self.__flvdemux.set_state(Gst.State.NULL)
        self.__audio_tee.set_state(Gst.State.NULL)
        self.__video_tee.set_state(Gst.State.NULL)

        self.__rtmp_src.unlink(self.__flvdemux)
        self.__flvdemux.unlink(self.__audio_tee)
        self.__flvdemux.unlink(self.__video_tee)
        self.__audio_tee.unlink(self.__audio_pad)
        self.__video_tee.unlink(self.__video_pad)

        for pad in self.__output_audio_pads:
            pad.unlink(self.__audio_tee)
            Gst.Object.unref(pad)

        for pad in self.__output_video_pads:
            pad.unlink(self.__video_tee)
            Gst.Object.unref(pad)

        Gst.Object.unref(self.__rtmp_src)
        Gst.Object.unref(self.__flvdemux)
        Gst.Object.unref(self.__audio_tee)
        Gst.Object.unref(self.__video_tee)

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
            self.__on_audio_pad_added(element, pad)

        elif name.startswith("video"):
            self.__on_video_pad_added(element, pad)
        else:
            self.__logger.debug("Unknown pad added")

    def __on_audio_pad_added(self, element, pad):
        self.__logger.debug("Audio pad added")
        self.__audio_pad = pad
        self.__create_audio_tee()
        self.__audio_pad.link(self.__audio_tee.get_static_pad("sink"))

    def __on_video_pad_added(self, element, pad):
        self.__logger.debug("Video pad added")
        self.__video_pad = pad
        self.__create_video_tee()
        self.__video_pad.link(self.__video_tee.get_static_pad("sink"))

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

        # getting the audio and video pads
        output_audio_pad = self.__audio_tee.get_request_pad("src_%u")
        self.__output_audio_pads.append(output_audio_pad)

        output_video_pad = self.__video_tee.get_request_pad("src_%u")
        self.__output_video_pads.append(output_video_pad)

        # linking the pads to the callbacks
        self._on_audio_available(output_audio_pad)
        self._on_video_available(output_video_pad)

    def get_video_request_pad(self):
        video_pad = self.__video_tee.get_request_pad("src_%u")
        self.__output_video_pads.append(video_pad)
        return video_pad

    def get_audio_request_pad(self):
        audio_pad = self.__audio_tee.get_request_pad("src_%u")
        self.__output_audio_pads.append(audio_pad)
        return audio_pad
