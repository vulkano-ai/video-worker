from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from abc import abstractmethod
from lib.processing.gstreamer.elements.GstBaseElement import GstBaseElement
from gi.repository import Gst


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

    @abstractmethod
    def create(self):
        """
        Abstract method to create the element.
        """
        super().create()

    @abstractmethod
    def add_to_pipeline(self):
        """
        Abstract method to add the element to the pipeline.
        """
        super().add_to_pipeline()

    @abstractmethod
    def link(self):
        """
        Abstract method to link the element to the pipeline.
        """
        super().link()

    @abstractmethod
    def unlink(self):
        """
        Abstract method to unlink the element from the pipeline.
        """
        super().unlink()

    @abstractmethod
    def remove_from_pipeline(self):
        """
        Abstract method to remove the element from the pipeline.
        """
        super().remove_from_pipeline()

    @abstractmethod
    def set_state(self, state: Gst.State):
        """
        Abstract method to set the state of the element.
        """
        super().set_state(state)

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
