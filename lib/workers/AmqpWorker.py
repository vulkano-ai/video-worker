from threading import Event, Thread
# from lib import GstMultiStreamsClass
from lib import Logger, ConfigManager


class AmqpThread(Thread):

    def __init__(self, context=None, config=None, default_sleep=1):
        super(AmqpThread, self).__init__()
        self.logger = Logger().get_logger("AMQP thread")
        self.config_manager = ConfigManager()

        self.logger.debug("AMQP thread init", config=config,
                          default_sleep=default_sleep)

        self.__close_event = Event()
        self.__default_sleep = default_sleep

    def run(self):
        self.logger.debug("AMQP thread running")

        while not self.__close_event.is_set():
            try:

                self.logger.info("Waiting for AMQP messages")
                
                self.__close_event.wait(self.__default_sleep)

            except Exception as e:
                self.logger.error("Gst error {}".format(e))
                self.stop()
        self.logger.debug("Gst thread closed")

    def stop(self):
        self.__close_event.set()
