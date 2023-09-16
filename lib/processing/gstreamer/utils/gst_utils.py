from gi.repository import Gst, GObject, GLib
from lib import Logger

__logger = Logger().get_logger("GstPipelineUtils")

def make_gst_element(factoryname, name, printedname, detail=""):

    __logger.debug("Creating element {}, {}".format(name, factoryname))
    elm = Gst.ElementFactory.make(factoryname, name)
    if not elm:
        __logger.error("Unable to create " + printedname + " \n")
        if detail:
            __logger.error(detail=detail)
    return elm

