from lib.common.Logger import Logger
from .video.GstNvv4lDecoder import GstNvv4lDecoder
from .GstBaseDecoder import VideoEncodings
from lib.processing.gstreamer import utils as gst_utils
from gi.repository import Gst


class GstVideoDecoderFactory(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GstVideoDecoderFactory, cls).__new__(cls)
            cls._instance.__logger = Logger().get_logger("GstVideoDecoderFactory")
            cls._instance.__logger.debug("Creating GstVideoDecoderFactory")
        return cls._instance

    def create_video_decoder(
        self,
        pad: Gst.Pad = None,
        elem_id: int = None,
        gst_pipeline: Gst.Pipeline = None,
        on_decoder_ready: callable = None,
    ):
        self.__logger.debug("Creating video decoder")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))
        # extract media type
        media_type = caps.get_structure(0).get_name()
        self.__logger.debug("Media type: {}".format(media_type))
        
        # TODO:
        # check if the media type is supported
        # and create the corresponding decoder
        # selcting the best decoder based on device capabilities
        
        # FIXME: for now, we only support H264 decoding
        return self.__create_h264_decoder(
            pad=pad,
            elem_id=elem_id,
            gst_pipeline=gst_pipeline,
            on_decoder_ready=on_decoder_ready
        )
        
    
    def __create_h264_decoder(
        self,
        pad: Gst.Pad = None,
        elem_id: int = None,
        gst_pipeline: Gst.Pipeline = None,
        on_decoder_ready: callable = None,    
    ):
        self.__logger.debug("Creating H264 decoder")
        self.__logger.debug(f"nvv4l decoder available: {GstNvv4lDecoder.is_available(VideoEncodings.H264)}")
        nvv4l = GstNvv4lDecoder(
            pipeline=gst_pipeline,
            pad=pad,
            elem_id=elem_id,
            on_decoder_ready=on_decoder_ready
        )
        return nvv4l