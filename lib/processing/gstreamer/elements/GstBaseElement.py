from lib import Logger
from gi.repository import Gst


class GstBaseElement(object):
    """
    Base class for GStreamer elements.
    """
    __logger = None
    __pipeline: Gst.Pipeline = None
    __elem_id = None
    __gst_plugin_name = None

    def __init__(self, pipeline, elem_id=0):
        """
        Constructor for GstBaseElement.

        Args:
        - pipeline: GStreamer pipeline object.
        - elem_id: ID of the element.
        """
        super().__init__()
        self.__logger = Logger().get_logger("GstElement")
        self.__logger.debug("Creating Base element")
        self.__pipeline = pipeline
        self.__elem_id = elem_id
        self.__logger.debug("Base element created")

    @property
    def pipeline(self):
        """
        Getter method for pipeline.
        """
        return self.__pipeline

    @property
    def elem_id(self):
        """
        Getter method for elem_id.
        """
        return self.__elem_id

    @property
    def gst_plugin_name(self):
        """
        Getter method for gst_plugin_name.
        """
        return self.__gst_plugin_name
