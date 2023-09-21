from gi.repository import Gst, GObject, GLib
from lib import Logger


def make_gst_element(factoryname, name, printedname, detail=""):
    """
    Creates a GStreamer element with the given factoryname and name.

    Args:
        factoryname (str): The name of the GStreamer factory to use.
        name (str): The name to give to the created element.
        printedname (str): The name of the element to print in error messages.
        detail (str, optional): Additional detail to print in error messages. Defaults to "".

    Returns:
        Gst.Element: The created GStreamer element, or None if creation failed.

    Description:
        This function creates a GStreamer element with the given factoryname and name. It is used to create GStreamer elements
        in the livestream-ai-worker project. If the creation of the element fails, an error message is logged with the details
        provided in the 'detail' argument.
    """
    __logger = Logger().get_logger("GstPipelineUtils")
    __logger.debug("Creating element {}, {}".format(name, factoryname))
    elm = Gst.ElementFactory.make(factoryname, name)
    if not elm:
        __logger.error("Unable to create " + printedname + " \n")
        if detail:
            __logger.error(detail=detail)
    return elm
