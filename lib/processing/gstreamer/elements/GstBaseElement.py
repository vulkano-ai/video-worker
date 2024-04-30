from lib import Logger
from gi.repository import Gst
from abc import abstractmethod
from lib.processing.gstreamer.exceptions import GstExceptions


class GstBaseElement(object):
    """
    Base class for GStreamer elements.
    """
    __logger = None
    __pipeline: Gst.Pipeline = None
    __elem_id = None
    __gst_plugin_name = None
    __state = Gst.State.NULL

    def __init__(self, pipeline: Gst.Pipeline = None, elem_id=0):
        """
        Constructor for GstBaseElement.

        Args:
        - pipeline: GStreamer pipeline object.
        - elem_id: ID of the element.
        """
        super().__init__()
        assert pipeline is not None, "Pipeline must be provided"
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
    def state(self):
        """
        Getter method for state.
        """
        return self.__state

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

    @abstractmethod
    def create(self):
        """
        Abstract method to create the element.
        """
        pass

    @abstractmethod
    def add_to_pipeline(self):
        """
        Abstract method to add the element to the pipeline.
        """
        pass

    @abstractmethod
    def link(self):
        """
        Abstract method to link the element to the pipeline.
        """
        pass

    @abstractmethod
    def unlink(self):
        """
        Abstract method to unlink the element from the pipeline.
        """
        pass

    @abstractmethod
    def remove_from_pipeline(self):
        """
        Abstract method to remove the element from the pipeline.
        """
        pass

    @abstractmethod
    def set_state(self, state: Gst.State):
        """
        Abstract method to set the state of the element.
        """
        self.__logger.debug("Setting state of %s to %s" % (self, state))
        self.__state = state
        pass

    def _add_element_to_pipeline(self, element: Gst.Element):
        """
        Adds the element to the pipeline.

        Args:
        - element: GStreamer element to add to the pipeline.
        """
        self.__logger.debug("Adding element %s to pipeline" % element)
        ret = self.pipeline.add(element)
        self.__logger.debug("Add response: %s" % ret)
        # if not ret:
        #     self.__logger.error(
        #         "Could not add element %s to pipeline" % element)
        #     raise GstExceptions.GstAddElementException(element)
        self.__logger.debug("Element %s added to pipeline" % element)

    def _make_gst_element(self, factory_name, name):
        """
        Creates a GStreamer element with the given name and factory name.

        Args:
        - name: Name of the element.
        - factory_name: Factory name of the element.
        """
        self.__logger.debug("Creating element %s, %s" % (name, factory_name))
        elm = Gst.ElementFactory.make(factory_name, name)
        if not elm:
            self.__logger.error("Unable to create element",
                                name=name, factory_name=factory_name)
            raise GstExceptions.GstCreateElementException(name)
        self.__logger.debug("Element %s, %s created" %
                            (name, factory_name))
        return elm

    def _link_elements(self, src, sink):
        """
        Links the two elements.

        Args:
        - src: Source element.
        - sink: Sink element.
        """
        self.__logger.debug("Linking %s to %s" % (src, sink))
        if not src.link(sink):
            self.__logger.error("Could not link %s to %s" % (src, sink))
            raise GstExceptions.GstLinkException(src, sink)
        self.__logger.debug("Linked %s to %s" % (src, sink))

    def _link_pads(self, src, sink):
        """
        Links the two pads.

        Args:
        - src: Source pad.
        - sink: Sink pad.
        """
        self.__logger.debug("Linking %s to %s" % (src, sink))
        if src.link(sink) != Gst.PadLinkReturn.OK:
            self.__logger.error("Could not link %s to %s" % (src, sink))
            raise GstExceptions.GstPadLinkException(src, sink)
        self.__logger.debug("Linked %s to %s" % (src, sink))

    def _unlink_elements(self, src, sink):
        """
        Unlinks the two elements.

        Args:
        - src: Source element.
        - sink: Sink element.
        """
        self.__logger.debug("Unlinking %s from %s" % (src, sink))
        if not src.unlink(sink):
            self.__logger.error("Could not unlink %s from %s" % (src, sink))
            raise GstExceptions.GstUnlinkException(src, sink)
        self.__logger.debug("Unlinked %s from %s" % (src, sink))

    def _unlink_pads(self, src, sink):
        """
        Unlinks the two pads.

        Args:
        - src: Source pad.
        - sink: Sink pad.
        """

        self.__logger.debug("Unlinking %s from %s" % (src, sink))
        if not src.unlink(sink):
            self.__logger.error("Could not unlink %s from %s" % (src, sink))
            raise GstExceptions.GstPadUnlinkException(src, sink)
        self.__logger.debug("Unlinked %s from %s" % (src, sink))

    def _set_element_state(self, element, state):
        """
        Sets the state of the element.

        Args:
        - element: GStreamer element.
        - state: State to set the element to.
        """
        self.__logger.debug("Setting state of %s to %s" % (element, state))
        if element.set_state(state) == Gst.StateChangeReturn.FAILURE:
            self.__logger.error("Could not set state of %s to %s" %
                                (element, state))
            raise GstExceptions.GstStateChangeException(element, state)
        self.__logger.debug("State of %s set to %s" % (element, state))

    def _remove_from_pipeline(self, element):
        """
        Removes the element from the pipeline.

        Args:
        - element: GStreamer element.
        """
        self.__logger.debug("Removing %s from pipeline" % element)
        if not self.pipeline.remove(element):
            self.__logger.error("Could not remove %s from pipeline" % element)
            raise GstExceptions.GstRemoveElementException(element)
        self.__logger.debug("Removed %s from pipeline" % element)
