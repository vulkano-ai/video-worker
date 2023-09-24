from abc import abstractmethod

from gi.repository import Gst, GObject, GLib
from lib import Logger


class GstPipelineRunner(object):
    """
    A class representing a GStreamer pipeline runner. It allows to run a GStreamer pipeline in a blocking manner.

    Attributes:
        __mainloop (GLib.MainLoop): The main loop of the pipeline.
        __pipeline (Gst.Pipeline): The GStreamer pipeline.
        __logger (Logger): The logger object for the pipeline.
        error_callback (function): The function to be called when an error occurs.
        eos_callback (function): The function to be called when the end of the stream is reached.
        state_change_callback (function): The function to be called when the state of the pipeline changes.

    Methods:
        __init__(self, error_callback=None, eos_callback=None, state_change_callback=None): Initializes the pipeline.
        __init_gst(self): Initializes GStreamer.
        __init_pipeline(self): Initializes the pipeline.
        __configure_signals(self): Configures the signals for the pipeline.
        _add_element(self, element): Adds an element to the pipeline.
        run_blocking(self): Runs the pipeline in a blocking manner.
        stop_pipeline(self): Stops the pipeline.
        on_eos(self, _bus, message): Callback function for end of stream signal.
        on_error(self, _bus, message): Callback function for error signal.
        quit(self, _bus=None, _message=None): Quits the main loop.
        on_state_change(self, _bus, message): Callback function for state change signal.
        set_playing(self): Sets the pipeline state to PLAYING.
        set_null(self): Sets the pipeline state to NULL.
        build_pipeline(self): Abstract method for building the pipeline.
    """
    __mainloop = None
    __gst_pipeline = None
    __logger = None

    def __init__(self, error_callback=None, eos_callback=None, state_change_callback=None):
        """
        Initializes the pipeline runner.

        Args:
            error_callback (function): The function to be called when an error occurs.
            eos_callback (function): The function to be called when the end of the stream is reached.
            state_change_callback (function): The function to be called when the state of the pipeline changes.
        """
        self.__logger = Logger().get_logger("GstPipelineRunner")
        self.__mainloop = None
        self.__gst_pipeline = None
        self.error_callback = error_callback or self.quit
        self.eos_callback = eos_callback or self.quit
        self.state_change_callback = state_change_callback
        self.__init_gst()
        self.__init_pipeline()

    def __init_gst(self):
        """
        Initializes GStreamer.
        """
        self.__logger.debug("Standard GStreamer initialization")
        Gst.init(None)
        GObject.threads_init()
        self.__mainloop = GLib.MainLoop()

    def __init_pipeline(self):
        """
        Initializes the pipeline.
        """
        self.__logger.debug("Creation pipeline")
        self.__gst_pipeline = Gst.Pipeline()
        if not self.__gst_pipeline:
            raise ValueError(" Unable to create Pipeline \n")

    def __configure_signals(self):
        """
        Configures the signals for the pipeline.
        """
        self.__logger.debug('configuring pipeline')
        bus = self.__gst_pipeline.bus

        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        bus.connect("message::state-changed", self.on_state_change)

    def _add_element(self, element):
        """
        Adds an element to the pipeline.

        Args:
            element (Gst.Element): The element to be added to the pipeline.
        """
        self.__logger.debug("Adding element {}".format(element.get_name()))
        self.__gst_pipeline.add(element)

    def run_blocking(self):
        """
        Runs the pipeline in a blocking manner.
        """
        self.__configure_signals()
        self.set_playing()

        try:
            self.__mainloop.run()
        except BaseException as e:
            print(e.__context__)
            pass

        self.set_null()

    def stop_pipeline(self):
        """
        Stops the pipeline.
        """
        self.__logger.debug("Stopping pipeline")
        self.set_null()
        self.quit()

    def on_eos(self, _bus, message):
        """
        Callback function for end of stream signal.

        Args:
            _bus (Gst.Bus): The bus object.
            message (Gst.Message): The message object.
        """
        self.__logger.error("EOS from {} (at {})".format(
            message.src.name, message.src.get_path_string()))
        self.eos_callback()

    def on_error(self, _bus, message):
        """
        Callback function for error signal.

        Args:
            _bus (Gst.Bus): The bus object.
            message (Gst.Message): The message object.
        """
        (error, debug) = message.parse_error()
        self.__logger.error(
            "Error from {} (at {})\n{} ({})".format(message.src.name, message.src.get_path_string(), error, debug))
        self.error_callback(_bus, message)

    def quit(self, _bus=None, _message=None):
        """
        Quits the main loop.

        Args:
            _bus (Gst.Bus): The bus object.
            _message (Gst.Message): The message object.
        """
        self.__logger.warning('quitting mainloop')
        self.__mainloop.quit()

    def on_state_change(self, _bus, message):
        """
        Callback function for state change signal.

        Args:
            _bus (Gst.Bus): The bus object.
            message (Gst.Message): The message object.
        """
        old_state, new_state, pending = message.parse_state_changed()
        if message.src == self.__gst_pipeline:
            self.__logger.info("Pipeline: State-Change from %s to %s; pending %s",
                               old_state.value_name, new_state.value_name, pending.value_name)
        else:
            self.__logger.debug("%s: State-Change from %s to %s; pending %s",
                                message.src.name, old_state.value_name, new_state.value_name, pending.value_name)

        if self.state_change_callback is not None:
            self.state_change_callback(_bus, message)

    def set_playing(self):
        """
        Sets the pipeline state to PLAYING.
        """
        self.__logger.info('requesting state-change to PLAYING')
        self.__gst_pipeline.set_state(Gst.State.PLAYING)

    def set_null(self):
        """
        Sets the pipeline state to NULL.
        """
        self.__logger.info('requesting state-change to NULL')
        self.__gst_pipeline.set_state(Gst.State.NULL)

    @abstractmethod
    def build_pipeline(self):
        """
        Abstract method for building the pipeline.
        """
        pass

    @property
    def gst_pipeline(self):
        """
        Returns the pipeline object.

        Returns:
            Gst.Pipeline: The pipeline object.
        """
        return self.__gst_pipeline
