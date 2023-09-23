# https://gstreamer.freedesktop.org/documentation/vaapi/index.html?gi-language=c
# https://gstreamer.freedesktop.org/documentation/vaapi/vaapidecodebin.html?gi-language=c
#
# supported inputs:
#    video/mpeg:
#        mpegversion: 2
#    systemstream: false
#    video/mpeg:
#        mpegversion: 4
#    video/x-divx:
#    video/x-xvid:
#    video/x-h263:
#    video/x-h264:
#    video/x-h265:
#    video/x-wmv:
#    video/x-vp8:
#    video/x-vp9:

from lib import Logger
from lib.processing.gstreamer.elements.codecs.decoders.GstBaseDecoder import GstBaseDecoder, VideoEncodings, GstDecoderClass
from lib.processing.gstreamer.utils.gst_utils import make_gst_element


class VaapiDeinterlaceMethod(object):
    AUTO = 0 # Auto detection
    INTERLACED = 1 # Force interlaced
    DISABLED = 2 # Never deinterlace

class GstVaapiDecoder(GstBaseDecoder):

    __logger = None
    __decoder = None
    __deinterlace_mode = None
    __disable_vpp = None
    __output_tee = None
    __supported_encodings = [
        VideoEncodings.H264, 
        VideoEncodings.H265, 
        VideoEncodings.JPEG, 
        VideoEncodings.MJPEG, 
        VideoEncodings.MPEG2, 
        VideoEncodings.MPEG4,
        VideoEncodings.VP8,
        VideoEncodings.VP9
    ]

    def __init__(self, pipeline=None, elem_id=0):
        super().__init__(
            pipeline=pipeline,
            elem_id=elem_id,
            name='vaapidecode',
            decoder_class=GstDecoderClass.VAAPI,
            supported_encodings=self.__supported_encodings
        )
        self.__logger = Logger().get_logger("GstVaapiDecoder")
    
    def init_decoder(self, deinterlace_mode: VaapiDeinterlaceMethod = VaapiDeinterlaceMethod.AUTO, disable_vpp=False):
        self.__logger.debug("Initializing vaapi decoder")
        self.__deinterlace_mode = deinterlace_mode
        self.__disable_vpp = disable_vpp
        self.__create_decoder()
        self.__configure_decoder()
        self.__create_output_tee()
        self.__logger.debug("vaapi decoder initialized")

    def __create_decoder(self):
        self.__logger.debug("Creating vaapidecodebin decoder")
        self.__decoder = make_gst_element(
            'vaapidecodebin', 'vaapidecodebin-%u' % self.elem_id)
        self.__logger.debug("vaapi decoder created")
        self.pipeline.add(self.__decoder)

    def __create_output_tee(self):
        self.__logger.debug("Creating output tee")
        self.__output_tee = make_gst_element(
            'tee', 'vaapidecodebin-output-tee-%u' % self.elem_id)
        self.__logger.debug("Output tee created")

    def __configure_decoder(self):
        self.__logger.debug("Configuring vaapi decoder")
        
        self.__decoder.set_property('deinterlace', self.__deinterlace_mode)
        self.__decoder.set_property('disable-vpp', self.__disable_vpp)
        self.__logger.debug("vaapi decoder configured")
    
    @property
    def tee(self):
        return self.__output_tee
    
    @property
    def deinterlace_mode(self):
        return self.__deinterlace_mode
    
    @property
    def decoder(self):
        return self.__decoder
    
    @property
    def supported_encodings(self):
        return self.__supported_encodings
    