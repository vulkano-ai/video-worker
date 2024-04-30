
class GstException(Exception):
    """Base class for all exceptions raised by this module."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class GstCreateElementException(GstException):
    """Exception raised when an element could not be created."""

    def __init__(self, element_name):
        self.element_name = element_name

    def __str__(self):
        return "Could not create element %s" % self.element_name


class GstLinkException(GstException):
    """Exception raised when a link between two elements fails."""

    def __init__(self, src, sink):
        self.src = src
        self.sink = sink

    def __str__(self):
        return "Could not link %s to %s" % (self.src, self.sink)


class GstUnlinkException(GstException):
    """Exception raised when an unlink between two elements fails."""

    def __init__(self, src, sink):
        self.src = src
        self.sink = sink

    def __str__(self):
        return "Could not unlink %s from %s" % (self.src, self.sink)


class GstPadLinkException(GstException):
    """Exception raised when a link between two pads fails."""

    def __init__(self, src, sink):
        self.src = src
        self.sink = sink

    def __str__(self):
        return "Could not link %s to %s" % (self.src, self.sink)


class GstPadUnlinkException(GstException):
    """Exception raised when an unlink between two pads fails."""

    def __init__(self, src, sink):
        self.src = src
        self.sink = sink

    def __str__(self):
        return "Could not unlink %s from %s" % (self.src, self.sink)


class GstStateChangeException(GstException):
    """Exception raised when a state change fails."""

    def __init__(self, element, state):
        self.element = element
        self.state = state

    def __str__(self):
        return "Could not change state of %s to %s" % (self.element, self.state)


class GstAddElementException(GstException):
    """Exception raised when an element could not be added to the pipeline."""

    def __init__(self, element):
        self.element = element

    def __str__(self):
        return "Could not add element %s to pipeline" % self.element


class GstRemoveElementException(GstException):
    """Exception raised when an element could not be removed from the pipeline."""

    def __init__(self, element):
        self.element = element

    def __str__(self):
        return "Could not remove element %s from pipeline" % self.element
