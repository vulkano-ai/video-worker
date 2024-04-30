from threading import Event, Thread
from lib import Logger, ConfigManager
import functools
import inference.pipeline.pipeline_pb2 as Pipeline
from queue import Queue
import time
import pika
from pika.exchange_type import ExchangeType
from lib.amqp.AmqpConsumer import AmqpConsumer
import logging


# disable pika debug logs
logging.getLogger("pika").setLevel(logging.WARNING)


class AmqpThread(Thread):
    """
    A thread class that handles AMQP connection and channel creation, queue initialization, and message consumption.

    Attributes:
        __connection (BlockingConnection): The AMQP connection object.
        __channel (BlockingConnection.channel): The AMQP channel object.
        __config (dict): The AMQP configuration dictionary.
        __logger (Logger): The logger object for logging AMQP thread events.
        __internal_queue (Queue): The queue object for storing AMQP messages.
        __close_event (Event): The event object for stopping the AMQP thread.

    Args:
        context (dict): The context dictionary for the AMQP thread.
        default_sleep (int): The default sleep time for the AMQP thread.
    """

    __config = None
    __logger = None
    __internal_queue = None
    __close_event = None
    __consumer = None
    __sleep_timeout = None

    def __init__(self, queue: Queue = None, default_sleep=0.5):
        super(AmqpThread, self).__init__()
        self.__logger = Logger().get_logger("AMQP thread")
        self.__logger.debug("AMQP thread init", default_sleep=default_sleep)
        self.__config = ConfigManager().get_amqp_config()
        self.__close_event = Event()
        self.__internal_queue = queue
        self.__consumer = self.__get_new_consumer()
        self.__sleep_time = default_sleep

        self.__logger.debug("AMQP thread init completed")

    def run(self):
        """
        The main method that runs the AMQP thread. It creates the AMQP connection and channel, initializes the queue,
        and consumes messages from the queue.
        """
        self.__logger.debug("AMQP thread running")
        while not self.__close_event.is_set() and not self.__consumer.stopping:
            try:
                self.__logger.info(
                    "AMQP successfully configured. Waiting for messages...")
                self.__consumer.run()
                self.__close_event.wait(self.__sleep_time)

            except Exception as e:
                self.__logger.error("AMQP error {}".format(e))
                self.__maybe_reconnect()

        self.__logger.debug("AMQP thread closed")

    def __on_pipeline_message(self, channel, method, properties, body):
        """
        A private method that handles the AMQP message consumption.

        Args:
            channel (BlockingConnection.channel): The AMQP channel object.
            method (pika.spec.Basic.Deliver): The AMQP delivery method.
            properties (pika.spec.BasicProperties): The AMQP message properties.
            body (bytes): The AMQP message body.
        """
        try:

            pipeline_request = Pipeline.StartPipelineRequest()
            pipeline_request.ParseFromString(body)
            self.__logger.debug("AMQP message received")
            self.__logger.debug("AMQP message body",
                                pipeline_request=pipeline_request)
            self.__logger.debug("AMQP message properties",
                                properties=properties)
            self.__logger.debug("AMQP message method", method=method)
            self.__logger.debug("AMQP message channel", channel=channel)

            self.__internal_queue.put(pipeline_request)
            self.__logger.debug("AMQP message added to internal queue")
        except Exception as e:
            self.__logger.error("AMQP error {}".format(e))

    def __get_new_consumer(self):
        self.__logger.debug("Creating new AMQP consumer",
                            amqp_url=self.__config.get_connection_string())
        return AmqpConsumer(
            amqp_url=self.__config.get_connection_string(),
            exchange_type=ExchangeType.direct,
            queue=self.__config.get_livestream_pipeline_queue(),
            routing_key="",
            exchange="",
            on_message_callback=self.__on_pipeline_message,
        )

    def __maybe_reconnect(self):
        if self._consumer.should_reconnect:
            self._consumer.stop()
            reconnect_delay = self.__get_reconnect_delay()
            self.__logger.info(
                'Reconnecting after %d seconds', reconnect_delay)
            time.sleep(reconnect_delay)
            self.__consumer = self.__get_new_consumer()

    def __get_reconnect_delay(self):
        if self.__consumer.was_consuming:
            self.__reconnect_delay = 0
        else:
            self.__reconnect_delay += 1
        if self.__reconnect_delay > 30:
            self.__reconnect_delay = 30
        return self.__reconnect_delay

    def stop(self):
        """
        A method that stops the AMQP thread.
        """
        self.__logger.debug("Stopping AMQP thread")
        self.__consumer.stop()
