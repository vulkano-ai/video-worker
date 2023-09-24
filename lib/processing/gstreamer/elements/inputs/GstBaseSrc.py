from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from abc import abstractmethod
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement


class GstBaseSrc(GstBaseElement):
    """
    Base class for GStreamer source elements.

    Attributes:
    - __logger: Logger object for logging messages.
    - __on_video_available: Callback function to be called when video is available.
    - __on_audio_available: Callback function to be called when audio is available.

    Methods:
    - __init__(self, pipeline, elem_id=0, on_video_available=None, on_audio_available=None): Constructor for GstBaseSrc class.
    - build_source(self): Abstract method to build the source element.
    - on_video_available(self): Getter method for on_video_available callback function.
    - on_audio_available(self): Getter method for on_audio_available callback function.
    """

    __logger = None

    __on_video_available = None
    __on_audio_available = None

    def __init__(self, pipeline, elem_id=0, on_video_available=None, on_audio_available=None):
        """
        Constructor for GstBaseSrc class.

        Args:
        - pipeline: GStreamer pipeline object.
        - elem_id: ID of the element.
        - on_video_available: Callback function to be called when video is available.
        - on_audio_available: Callback function to be called when audio is available.
        """
        super().__init__(pipeline, elem_id)
        self.__logger = Logger().get_logger("GstBaseSrc")
        self.__logger.debug("GstBaseSrc init started")
        assert on_video_available is not None or on_audio_available is not None, "At least one callback must be provided"

        self.__on_video_available = on_video_available
        self.__on_audio_available = on_audio_available
        self.__logger.debug("GstBaseSrc init completed")

    @property
    def _on_video_available(self):
        """
        Getter method for on_video_available callback function.
        """
        return self.__on_video_available

    @property
    def _on_audio_available(self):
        """
        Getter method for on_audio_available callback function.
        """
        return self.__on_audio_available
