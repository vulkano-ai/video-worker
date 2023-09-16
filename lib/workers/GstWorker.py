from threading import Event, Thread
from lib import Logger, ConfigManager
from inference import pipeline
import logging


class GstThread(Thread):

    def __init__(self, config=None, default_sleep=1):
        super(GstThread, self).__init__()
        self.logger = Logger().get_logger("Gst thread")
        self.config_manager = ConfigManager()

        self.logger.debug("GST thread init", config=config,
                          default_sleep=default_sleep)

        self.__close_event = Event()
        self.__default_sleep = default_sleep

    def run(self):
        self.logger.debug("Gst thread running")
        self.logger.info("Starting Gst Pipeline")
        while not self.__close_event.is_set():
            try:

                self.__close_event.wait(self.__default_sleep)

            except Exception as e:
                self.logger.error("Gst error {}".format(e))
                self.stop()
        self.logger.debug("Gst thread closed")

    def stop(self):
        self.__close_event.set()
