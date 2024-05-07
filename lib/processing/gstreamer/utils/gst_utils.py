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

    Example:
        To create a GStreamer element with the name 'myelement' and the factory name 'myfactory', you can call the function as follows:
        >>> make_gst_element('myfactory', 'myelement', 'My Element')
    """
    __logger = Logger().get_logger("GstPipelineUtils")
    __logger.debug("Creating element {}, {}".format(name, factoryname))
    elm = Gst.ElementFactory.make(factoryname, name)
    if not elm:
        __logger.error("Unable to create " + printedname + " \n")
        if detail:
            __logger.error(detail=detail)
    return elm


def is_plugin_available(plugin_name):
    """
    Checks if the given GStreamer plugin is available.

    Args:
        plugin_name (str): The name of the plugin to check.

    Returns:
        bool: True if the plugin is available, False otherwise.

    Description:
        This function checks if the given GStreamer plugin is available. It is used to check if GStreamer plugins are
        available in the livestream-ai-worker project.
    """
    __logger = Logger().get_logger("GstPipelineUtils")
    __logger.debug("Checking if plugin {} is available".format(plugin_name))
    registry = Gst.Registry.get()
    plugin = registry.find_plugin(plugin_name)
    if plugin is None:
        __logger.error("Plugin %s not found" % plugin_name)
        return False
    else:
        __logger.debug("Plugin %s found" % plugin_name)
        return True


def is_feature_available(plugin_name, feature_name):
    """
    Checks if the feature is available.
    """
    __logger = Logger().get_logger("GstPipelineUtils")

    registry = Gst.Registry.get()
    plugin = registry.find_plugin(plugin_name)
    if plugin is None:
        __logger.error("Plugin %s not found" % plugin_name)
        return False
    else:
        return True
        # __logger.debug("Plugin %s found" % plugin_name)
        # feature = registry.find_feature(feature_name, )
        # if feature is None:
        #     __logger.error("Feature %s not found" % feature_name)
        #     return False
        # else:
        #     __logger.debug("Feature %s found" % feature_name)
        #     return True
