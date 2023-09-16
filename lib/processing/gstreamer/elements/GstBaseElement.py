from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
from abc import abstractmethod


class GstBaseElement(object):
    __logger = None
    _pipeline = None
    _elem_id = None

    def __init__(self, pipeline, elem_id=0):
        super().__init__()
        self.__logger = Logger().get_logger("GstElementSink")
        self.__logger.debug("Creating Base element")
        self._pipeline = pipeline
        self._elem_id = elem_id
