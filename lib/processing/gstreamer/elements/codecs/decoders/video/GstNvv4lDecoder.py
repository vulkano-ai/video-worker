# https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvvideo4linux2.html
# The OSS Gst-nvvideo4linux2 plugin leverages the hardware decoding engines on Jetson and DGPU platforms by interfacing with libv4l2 plugins on those platforms. It supports H.264, H.265, JPEG and MJPEG formats. The plugin accepts an encoded bitstream and uses the NVDEC hardware engine to decode the bitstream. The decoded output can be NV12 or YUV444 format which depends on the encoded stream content.
# NOTE: When you use the v4l2 decoder for decoding JPEG images, you must use the open source jpegparse plugin before the decoder to parse encoded JPEG images.
# Inputs
#
# - An encoded bitstream. Supported formats are H.264, H.265, JPEG and MJPEG
# - H264 encoded bitstream in 8bit 4:2:0 format.
# - H265 encoded bitstream in 8/10/12 bit 4:2:0 and 8/10/12 bit 4:4:4 format.

# Outputs
#
# - H264 decoder outputs GstBuffer in 8bit semi-planar(NV12) 4:2:0 format.
# - H265 decoder outputs GstBuffer in 8/10/12 bit semi-planar(NV12) 4:2:0 format, 8/10/12 bit planar(YUV444) 4:4:4 format.

from lib import Logger
from lib.processing.gstreamer.elements.codecs.decoders.GstBaseDecoder import GstBaseDecoder, VideoEncodings, GstDecoderClass
from lib.processing.gstreamer.utils import gst_utils
from gi.repository import Gst


class CudaMemoryType(object):
    DEVICE = 0
    PINNED = 1
    UNIFIED = 2

supported_encodings = [
        VideoEncodings.H264,
        VideoEncodings.H265,
        # VideoEncodings.JPEG,
        # VideoEncodings.MJPEG
    ]
class GstNvv4lDecoder(GstBaseDecoder):

    __supported_encodings = supported_encodings
    __decoder_class = GstDecoderClass.NVV4L2
    __parser = None
    __logger = None
    __decoder = None
    __gpu_id = None
    __memory_type = None
    __low_latency_mode = None
    __output_tee = None

    __src_pad = None
    __gst_plugin_name = 'nvvideo4linux2'
    __gst_feature_name = 'nvv4l2decoder'
    __on_decoder_ready = None

    def __init__(
            self,
            pipeline: Gst.Pipeline=None,
            pad: Gst.Pad=None,
            elem_id: int = 0,
            media_type: VideoEncodings = VideoEncodings.H264,
            on_decoder_ready=None
        ):
        super().__init__(
            pipeline=pipeline,
            elem_id=elem_id,
            decoder_class=self.__decoder_class,
            supported_encodings=self.__supported_encodings
        )
        self.__media_type = media_type
        self.__on_decoder_ready = on_decoder_ready
        self.__src_pad = pad
        self.__logger = Logger().get_logger("GstNvv4lDecoder")

    def init_decoder(self, gpu_id=0, memory_type: CudaMemoryType = CudaMemoryType.DEVICE, low_latency_mode=True):
        self.__logger.debug("Initializing nvv4l decoder")
        self.__gpu_id = gpu_id
        self.__memory_type = memory_type
        self.__low_latency_mode = low_latency_mode
        self.__create_parser()
        self.__create_queue()
        self.__create_nvv4l_decoder()
        self.__create_output_tee()
        self.__configure_decoder()
        self.__add_elements_to_pipeline()
        self.__link_elements()
        self.__sync_elements()

        fake_sink = self._make_gst_element('fakesink', 'fakesink-%u' % self.elem_id)
        fake_sink.set_property('sync', False)
        self.pipeline.add(fake_sink)
        self.tee.link(fake_sink)
        fake_sink.sync_state_with_parent()
        self.__logger.debug("nvv4l decoder initialized")

    def __create_parser(self):
        self.__logger.debug("Creating parser")
        self.__parser = self._make_gst_element('h264parse', 'h264parse-%u' % self.elem_id)
        self.__logger.debug("Parser created")
                                                   
    def __create_queue(self):
        self.__logger.debug("Creating queue")
        self.__queue = self._make_gst_element('queue', 'queue-nvv4l-%u' % self.elem_id)
        self.__logger.debug("Queue created")

    def __create_nvv4l_decoder(self):
        self.__logger.debug("Creating nvv4l decoder")
        self.__decoder = self._make_gst_element(
            'nvv4l2decoder', 'nvv4l2dec-%u' % self.elem_id)
        self.__logger.debug("nvv4l decoder created")

    def __create_output_tee(self):
        self.__logger.debug("Creating output tee")
        self.__output_tee = self._make_gst_element(
            'tee', 'nvv4l2dec-output-tee-%u' % self.elem_id)
        self.__logger.debug("Output tee created")

    def __configure_decoder(self):
        self.__logger.debug("Configuring nvv4l decoder")
        self.__decoder.set_property('gpu-id', self.__gpu_id)
        self.__decoder.set_property('num-extra-surfaces', 0)
        self.__decoder.set_property('skip-frames', 0)
        self.__decoder.set_property('drop-frame-interval', 0)
        self.__decoder.set_property('cudadec-memtype', self.__memory_type)
        self.__decoder.set_property(
            'low-latency-mode', self.__low_latency_mode)
        self.__logger.debug("nvv4l decoder configured")

    def __add_elements_to_pipeline(self):
        self.__logger.debug("Adding elements to pipeline")
        self.pipeline.add(self.parser)
        self.pipeline.add(self.queue)
        self.pipeline.add(self.decoder)
        self.pipeline.add(self.tee)
        self.__logger.debug("Elements added to pipeline")

    def __link_elements(self):
        self.__logger.debug("Linking elements")
        self.__src_pad.link(self.parser.get_static_pad('sink'))
        self.parser.link(self.queue)
        self.queue.link(self.decoder)
        self.decoder.link(self.tee)
        self.__logger.debug("Elements linked")

    def __sync_elements(self):
        self.__logger.debug("Syncing elements")
        self.parser.sync_state_with_parent()
        self.queue.sync_state_with_parent()
        self.decoder.sync_state_with_parent()
        self.tee.sync_state_with_parent()
        self.__logger.debug("Elements synced")
    @property
    def parser(self):
        return self.__parser
    
    @property
    def queue(self):
        return self.__queue
    @property
    def decoder(self):
        return self.__decoder

    @property
    def gpu_id(self):
        return self.__gpu_id

    @property
    def memory_type(self):
        return self.__memory_type

    @property
    def low_latency_mode(self):
        return self.__low_latency_mode

    @property
    def tee(self):
        return self.__output_tee

    def on_video_available(self, callback):
        # link elements
        pass
    
    @property
    def supported_encodings(self):
        return self.__supported_encodings
    
    @staticmethod
    def is_available(media_type: VideoEncodings):

        if not gst_utils.is_plugin_available('nvvideo4linux2'):
            return False

        if not gst_utils.is_feature_available('nvvideo4linux2', 'nvv4l2decoder'):
            return False

        if media_type not in supported_encodings:
            return False

        return True
