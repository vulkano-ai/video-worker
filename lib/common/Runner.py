import logging

from gi.repository import Gst, GObject, GLib
from lib import Logger


class Runner(object):
    def __init__(self, pipeline, error_callback=None):
        self.__logger__ = Logger().get_logger("Runner")
        self.mainloop = GLib.MainLoop()
        self.pipeline = pipeline
        self.error_callback = error_callback or self.quit

    def run_blocking(self):
        self.configure()
        self.set_playing()

        try:
            self.mainloop.run()
        # except KeyboardInterrupt:
        #     print('Terminated via Ctrl-C')
        except BaseException as e:
            print(e.__context__)
            pass

        self.set_null()

    def configure(self):
        self.__logger__.debug('configuring pipeline')
        bus = self.pipeline.bus

        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)
        bus.connect("message::state-changed", self.on_state_change)

    def on_eos(self, _bus, message):
        self.__logger__.error("EOS from {} (at {})".format(
                  message.src.name, message.src.get_path_string()))
        self.error_callback()

    def on_error(self, _bus, message):
        (error, debug) = message.parse_error()
        self.__logger__.error("Error from {} (at {})\n{} ({})".format(message.src.name, message.src.get_path_string(), error, debug))
        self.error_callback()

    def quit(self):
        self.__logger__.warning('quitting mainloop')
        self.mainloop.quit()

    def on_state_change(self, _bus, message):
        old_state, new_state, pending = message.parse_state_changed()
        if message.src == self.pipeline:
            self.__logger__.info("Pipeline: State-Change from %s to %s; pending %s",
                     old_state.value_name, new_state.value_name, pending.value_name)
        else:
            self.__logger__.debug("%s: State-Change from %s to %s; pending %s",
                      message.src.name, old_state.value_name, new_state.value_name, pending.value_name)

    def set_playing(self):
        self.__logger__.info('requesting state-change to PLAYING')
        self.pipeline.set_state(Gst.State.PLAYING)

    def set_null(self):
        self.__logger__.info('requesting state-change to NULL')
        self.pipeline.set_state(Gst.State.NULL)