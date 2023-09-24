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


class CudaMemoryType(object):
    DEVICE = 0
    PINNED = 1
    UNIFIED = 2


class GstNvv4lDecoder(GstBaseDecoder):

    __supported_encodings = [
        VideoEncodings.H264,
        VideoEncodings.H265,
        # VideoEncodings.JPEG,
        # VideoEncodings.MJPEG
    ]
    __decoder_class = GstDecoderClass.NVV4L2

    __logger = None
    __decoder = None
    __gpu_id = None
    __memory_type = None
    __low_latency_mode = None
    __output_tee = None
    __gst_plugin_name = 'nvvideo4linux2'
    __gst_feature_name = 'nvv4l2decoder'

    def __init__(self, pipeline=None, elem_id=0):
        super().__init__(
            pipeline=pipeline,
            elem_id=elem_id,
            decoder_class=self.__decoder_class,
            supported_encodings=self.__supported_encodings
        )
        self.__logger = Logger().get_logger("GstNvv4lDecoder")

    def init_decoder(self, gpu_id=0, memory_type: CudaMemoryType = CudaMemoryType.DEVICE, low_latency_mode=True):
        self.__logger.debug("Initializing nvv4l decoder")
        self.__gpu_id = gpu_id
        self.__memory_type = memory_type
        self.__low_latency_mode = low_latency_mode
        self.__create_nvv4l_decoder()
        self.__create_output_tee()
        self.__configure_decoder()
        self.__logger.debug("nvv4l decoder initialized")

    def __create_nvv4l_decoder(self):
        self.__logger.debug("Creating nvv4l decoder")
        self.__decoder = gst_utils.make_gst_element(
            'nvv4l2decoder', 'nvv4l2dec-%u' % self.elem_id)
        self.__logger.debug("nvv4l decoder created")

    def __create_output_tee(self):
        self.__logger.debug("Creating output tee")
        self.__output_tee = gst_utils.make_gst_element(
            'tee', 'nvv4l2dec-output-tee-%u' % self.elem_id)
        self.__logger.debug("Output tee created")

    def __configure_decoder(self):
        self.__logger.debug("Configuring nvv4l decoder")
        self.__decoder.set_property('gpu-id', self.__gpu_id)
        self.__decoder.set_property('num-extra-surfaces', 0)
        self.__decoder.set_property('skip-frames', 0)
        self.__decoder.set_property('drop-frame-interval', 0)
        self.__decoder.set_property('cuda-memory-type', self.__memory_type)
        self.__decoder.set_property(
            'low-latency-mode', self.__low_latency_mode)
        self.__logger.debug("nvv4l decoder configured")

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

    def is_available(self, media_type):

        if not gst_utils.is_plugin_available(self.__gst_plugin_name):
            return False

        if not gst_utils.is_feature_available(self.__gst_feature_name):
            return False

        if media_type not in self.__supported_encodings:
            return False

        return True
