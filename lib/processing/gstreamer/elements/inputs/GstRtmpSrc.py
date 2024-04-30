from lib import Logger
from gi.repository import Gst
from .GstBaseSrc import GstBaseSrc
from lib.processing.gstreamer.exceptions.GstExceptions import GstLinkException
import random

class GstRtmpSrc(GstBaseSrc):
    """
    A GStreamer element for receiving RTMP streams.

    Args:
        pipeline (Gst.Pipeline): The GStreamer pipeline to which this element belongs.
        source_id (int): The ID of this source element.
        on_video_available (function): A callback function to be called when video data is available.
        on_audio_available (function): A callback function to be called when audio data is available.
        location (str): The location of the RTMP stream.

    Attributes:
        __logger (Logger): The logger for this class.
        __location (str): The location of the RTMP stream.
        __rtmp_src (Gst.Element): The RTMP source element.
        __flvdemux (Gst.Element): The FLV demuxer element.
        __audio_tee (Gst.Element): The audio tee element.
        __video_tee (Gst.Element): The video tee element.
        __audio_pad (Gst.Pad): The audio pad.
        __video_pad (Gst.Pad): The video pad.
        __output_audio_pads (list): A list of audio output pads.
        __output_video_pads (list): A list of video output pads.
    """

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

    def __init__(self, pipeline: Gst.Pipeline, elem_id: int = 0, on_video_available: callable = None, on_audio_available: callable = None, location: str = None):
        super().__init__(
            pipeline=pipeline,
            elem_id=elem_id,
            on_video_available=on_video_available,
            on_audio_available=on_audio_available
        )

        self.__location = location

    def __del__(self):

        self.__logger.debug("Deleting rtmp src")
        self.set_state(Gst.State.NULL)
        self.unlink()
        self.remove_from_pipeline()

        for pad in self.__output_audio_pads:
            Gst.Object.unref(pad)

        for pad in self.__output_video_pads:
            Gst.Object.unref(pad)

        Gst.Object.unref(self.__rtmp_src)
        Gst.Object.unref(self.__flvdemux)
        Gst.Object.unref(self.__audio_tee)
        Gst.Object.unref(self.__video_tee)
        self.__logger.debug("Rtmp src deleted")

    def create(self):
        """
        Creates the GstRtmpSrc element and its related elements.
        """
        self.__logger.debug("Creating rtmp input")
        self.__queue = self._make_gst_element("queue2", f"rtmp-src-queue-{self.elem_id}")
        self.__create_rtmp_src()
        self.__create_audio_tee()
        self.__create_video_tee()
        self.__create_flvdemux()
        super().create()

    def add_to_pipeline(self):
        """
        Adds the GstRtmpSrc element and its related elements to the pipeline.
        """
        self.__logger.debug("Adding rtmp src to pipeline")
        self._add_element_to_pipeline(self.rtmp_src)
        self._add_element_to_pipeline(self.__queue)
        self._add_element_to_pipeline(self.flvdemux)
        self._add_element_to_pipeline(self.audio_tee)
        self._add_element_to_pipeline(self.video_tee)
        super().add_to_pipeline()

    def link(self):
        """
        Links the GstRtmpSrc element and its related elements to the pipeline.
        """
        self.__logger.debug("Linking rtmp src")
        self._link_elements(self.rtmp_src, self.__queue) 
        self._link_elements(self.__queue, self.flvdemux)
        super().link()

    def unlink(self):
        """
        Unlinks the elements in the pipeline in the following order:
        rtmp_src -> flvdemux -> audio_tee -> audio_pad
        flvdemux -> video_tee -> video_pad
        output_audio_pads -> audio_tee
        output_video_pads -> video_tee
        """

        self._unlink_elements(self.rtmp_src, self.flvdemux)
        self._unlink_elements(self.flvdemux, self.audio_tee)
        self._unlink_elements(self.flvdemux, self.video_tee)
        super().unlink()
        # for pad in self.__output_audio_pads:
        #     self._unlink_pads(pad, self.__audio_tee.get_static_pad("sink"))

        # for pad in self.__output_video_pads:
        #     pad.unlink(self.__video_tee)

    def remove_from_pipeline(self):
        """
        Remove the elements from the pipeline in the following order:
        rtmp_src -> flvdemux -> audio_tee, video_tee
        """

        self._remove_from_pipeline(self.rtmp_src)
        self._remove_from_pipeline(self.flvdemux)
        self._remove_from_pipeline(self.audio_tee)
        self._remove_from_pipeline(self.video_tee)
        super().remove_from_pipeline()

    def set_state(self, state: Gst.State):
        """
        Sets the state of the GstRtmpSrc element and its related elements.

        Args:
            state (Gst.State): The state to set the elements to.
        """
        self._set_element_state(self.rtmp_src, state)
        self._set_element_state(self.__queue, state)
        self._set_element_state(self.flvdemux, state)
        if self.audio_tee is not None:
            self._set_element_state(self.audio_tee, state)

        if self.video_tee is not None:
            self._set_element_state(self.video_tee, state)
        super().set_state(state)
    def __on_rtmp_pad_added(self, element, pad):
        self.__logger.debug(f"Pad added {random.random()}")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))

    def __create_rtmp_src(self):
        self.__logger.debug("Creating rtmp src")
        elem_name = "rtmp-src-%u" % self.elem_id
        self.__rtmp_src = self._make_gst_element("rtmpsrc", elem_name)
        self.rtmp_src.set_property("location", f"{self.location} live=1")

        self.rtmp_src.set_property("do-timestamp", True)
        self.rtmp_src.set_property("timeout", 0)


    def __create_flvdemux(self):
        elem_name = "flxdemux-rtmp-%u" % self.elem_id
        self.__flvdemux = self._make_gst_element("flvdemux", elem_name)
        self.flvdemux.connect("pad-added", self.__on_pad_added)
        self.flvdemux.connect("pad-removed", self.__on_pad_removed)
        self.flvdemux.connect("no-more-pads", self.__on_no_more_pads)

    def __create_audio_tee(self):
        elem_name = "rtmp-audio-tee-%u" % self.elem_id
        self.__audio_tee = self._make_gst_element("tee", elem_name)

    def __create_video_tee(self):
        elem_name = "rtmp-video-tee-%u" % self.elem_id
        self.__video_tee = self._make_gst_element("tee", elem_name)

    def __on_pad_added(self, element, pad):
        self.__logger.debug(f"Pad added {random.random()}")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        
        # check if the pad is already linked
        if pad.is_linked():
            self.__logger.debug("Pad already linked")
            self.set_state(Gst.State.PLAYING)
            return Gst.PadProbeReturn.OK
        fake_sink = self._make_gst_element("fakesink", f"fake-sink-tee{random.random()}")

        self._add_element_to_pipeline(fake_sink)
        fake_sink_pad = fake_sink.get_static_pad("sink")
        self._link_pads(pad, fake_sink_pad)


        #if name.startswith("audio"):
        #     self.__audio_pad = pad

        #     self.__on_audio_pad_added(element, pad)
        #     self.__logger.debug("Audio pad successfully handled")
        # elif name.startswith("video"):
        #     self.__video_pad = pad
        #     self.__on_video_pad_added(element, pad)
        #     self.__logger.debug("Video pad successfully handled")

        # else:
        #     self.__logger.debug("Unknown pad added")
        

    def __on_audio_pad_added(self, element, pad):
        self.__logger.debug("Audio pad added")
        if self.audio_pad is not None:
            return
        self.__audio_pad = pad
        sink_pad = self.audio_tee.get_static_pad("sink")
        self._link_pads(self.audio_pad, sink_pad)

        fake_sink = self._make_gst_element("fakesink", "fake-sink-audio-tee")
        self._add_element_to_pipeline(fake_sink)
        output_audio_pad = self.audio_tee.get_request_pad("src_%u")

        if output_audio_pad is not None:
            fake_sink_pad = fake_sink.get_static_pad("sink")
            self._link_pads(output_audio_pad, fake_sink_pad)
            self.__output_audio_pads.append(output_audio_pad)
            # self.set_state(Gst.State.PLAYING)
            # self._on_audio_available(output_audio_pad)
        else:
            self.__logger.debug(
                "No audio pad available for stream %u" % self.elem_id)

    def __on_video_pad_added(self, element, pad):
        self.__logger.debug("Video pad added")
        if self.video_pad is not None:
            return
        self.__video_pad = pad
        sink_pad = self.__video_tee.get_static_pad("sink")
        self._link_pads(self.video_pad, sink_pad)
        
        fake_sink = self._make_gst_element("fakesink", "fake-sink-video-tee")
        self._add_element_to_pipeline(fake_sink)
        
        output_video_pad = self.__video_tee.get_request_pad("src_%u")
        
        if output_video_pad is not None:
            fake_sink_pad = fake_sink.get_static_pad("sink")
            self._link_pads(output_video_pad, fake_sink_pad)
            self.__output_video_pads.append(output_video_pad)
            # self._on_video_available(output_video_pad)
            # self.set_state(Gst.State.PLAYING)
        else:
            self.__logger.debug(
                "No video pad available for stream %u" % self.elem_id)

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
        # CHECK: Is this necessary here or inside __on_pad_added?
        self.pipeline.set_state(Gst.State.PLAYING)

    def get_video_request_pad(self):
        video_pad = self.__video_tee.get_request_pad("src_%u")
        self.__output_video_pads.append(video_pad)
        return video_pad

    def get_audio_request_pad(self):
        audio_pad = self.__audio_tee.get_request_pad("src_%u")
        self.__output_audio_pads.append(audio_pad)
        return audio_pad

    @property
    def rtmp_src(self):
        """
        Getter method for rtmp_src element.
        """
        return self.__rtmp_src

    @property
    def flvdemux(self):
        """
        Getter method for flvdemux element.
        """
        return self.__flvdemux

    @property
    def audio_tee(self):
        """
        Getter method for audio_tee element.
        """
        return self.__audio_tee

    @property
    def video_tee(self):
        """
        Getter method for video_tee element.
        """
        return self.__video_tee

    @property
    def location(self):
        """
        Getter method for location.
        """
        return self.__location

    @property
    def audio_pad(self):
        """
        Getter method for audio_pad.
        """
        return self.__audio_pad

    @property
    def video_pad(self):
        """
        Getter method for video_pad.
        """
        return self.__video_pad

    @property
    def output_audio_pads(self):
        """
        Getter method for output_audio_pads.
        """
        return self.__output_audio_pads

    @property
    def output_video_pads(self):
        """
        Getter method for output_video_pads.
        """
        return self.__output_video_pads
