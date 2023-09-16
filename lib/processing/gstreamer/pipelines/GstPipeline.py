from abc import abstractmethod

from gi.repository import Gst, GObject, GLib
from lib import Logger


class GstPipeline(object):
    def __init__(self, error_callback=None, eos_callback=None, state_change_callback=None):
        self.__logger = Logger().get_logger("GstPipeline")
        self._mainloop = None
        self._pipeline = None
        self.error_callback = error_callback or self.quit
        self.eos_callback = eos_callback or self.quit
        self.state_change_callback = state_change_callback
        self.__init_gst()
        self.__init_pipeline()

    def __init_gst(self):
        self.__logger.debug("Standard GStreamer initialization")
        Gst.init(None)
        GObject.threads_init()
        self._mainloop = GLib.MainLoop()

    def __init_pipeline(self):
        self.__logger.debug("Creation pipeline")
        self._pipeline = Gst.Pipeline()
        if not self._pipeline:
            raise ValueError(" Unable to create Pipeline \n")

    def __configure_signals(self):
        self.__logger.debug('configuring pipeline')
        bus = self._pipeline.bus

        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        bus.connect("message::state-changed", self.on_state_change)

    def _add_element(self, element):
        self.__logger.debug("Adding element {}".format(element.get_name()))
        self._pipeline.add(element)

    def run_blocking(self):
        self.__configure_signals()
        self.set_playing()

        try:
            self._mainloop.run()
        # except KeyboardInterrupt:
        #     print('Terminated via Ctrl-C')
        except BaseException as e:
            print(e.__context__)
            pass

        self.set_null()

    def stop_pipeline(self):
        self.__logger.debug("Stopping pipeline")
        self.set_null()
        self.quit()
    def on_eos(self, _bus, message):
        self.__logger.error("EOS from {} (at {})".format(
            message.src.name, message.src.get_path_string()))
        self.eos_callback()

    def on_error(self, _bus, message):
        (error, debug) = message.parse_error()
        self.__logger.error(
            "Error from {} (at {})\n{} ({})".format(message.src.name, message.src.get_path_string(), error, debug))
        self.error_callback(_bus, message)

    def quit(self, _bus=None, _message=None):
        self.__logger.warning('quitting mainloop')
        self._mainloop.quit()

    def on_state_change(self, _bus, message):
        old_state, new_state, pending = message.parse_state_changed()
        if message.src == self._pipeline:
            self.__logger.info("Pipeline: State-Change from %s to %s; pending %s",
                               old_state.value_name, new_state.value_name, pending.value_name)
        else:
            self.__logger.debug("%s: State-Change from %s to %s; pending %s",
                                message.src.name, old_state.value_name, new_state.value_name, pending.value_name)

        if self.state_change_callback is not None:
            self.state_change_callback(_bus, message)

    def set_playing(self):
        self.__logger.info('requesting state-change to PLAYING')
        self._pipeline.set_state(Gst.State.PLAYING)

    def set_null(self):
        self.__logger.info('requesting state-change to NULL')
        self._pipeline.set_state(Gst.State.NULL)

    @abstractmethod
    def build_pipeline(self):
        pass
