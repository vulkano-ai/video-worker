from threading import Event, Thread
from lib import Logger, ConfigManager
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
import logging
import functools
import inference.pipeline.pipeline_pb2 as Pipeline


class AmqpThread(Thread):
    """
    A thread class that handles AMQP connection and channel creation, queue initialization, and message consumption.

    Attributes:
        __connection (BlockingConnection): The AMQP connection object.
        __channel (BlockingConnection.channel): The AMQP channel object.
        __config (dict): The AMQP configuration dictionary.
        __logger (Logger): The logger object for logging AMQP thread events.
        __close_event (Event): The event object for stopping the AMQP thread.

    Args:
        context (dict): The context dictionary for the AMQP thread.
        default_sleep (int): The default sleep time for the AMQP thread.
    """

    __connection = None
    __channel = None
    __config = None
    __logger = None

    def __init__(self, context=None, default_sleep=1):
        super(AmqpThread, self).__init__()
        self.__logger = Logger().get_logger("AMQP thread")
        self.__logger.debug("AMQP thread init", default_sleep=default_sleep)
        self.__config = ConfigManager().get_amqp_config()
        self.__close_event = Event()
        self.__logger.debug("AMQP thread init completed")
        logging.getLogger("pika").setLevel(logging.WARNING)

    def run(self):
        """
        The main method that runs the AMQP thread. It creates the AMQP connection and channel, initializes the queue,
        and consumes messages from the queue.
        """
        self.__logger.debug("AMQP thread running")
        self.__connection = self.__create_connection()
        self.__channel = self.__create_channel()
        self.__init_queue()

        # self.__connection.add_callback_threadsafe(self.__on_pipeline_message)
        self.__channel.basic_consume(
            queue=self.__config.get_livestream_pipeline_queue(),
            auto_ack=True,
            on_message_callback=self.__on_pipeline_message
        )
        try:
            self.__logger.info(
                "AMQP successfully configured. Waiting for messages...")
            self.__channel.start_consuming()
            self.__close_event.wait()

        except Exception as e:
            self.__logger.error("AMQP error {}".format(e))

        self.stop()
        self.__logger.debug("AMQP thread closed")

    def stop(self):
        """
        A method that stops the AMQP thread. It closes the channel and connection, sets the close event, and destroys
        the AMQP resources.
        """
        self.__logger.debug("Stopping AMQP thread")
        self.__close_channel()
        self.__close_connection()
        self.__close_event.set()
        self.__logger.debug("AMQP resources destroyed")

    def __create_connection(self):
        """
        A private method that creates the AMQP connection object.

        Returns:
            BlockingConnection: The AMQP connection object.
        """
        self.__logger.debug("Creating AMQP connection")
        credentials = PlainCredentials(
            self.__config.get_username(), self.__config.get_password())
        parameters = ConnectionParameters(
            self.__config.get_host(), self.__config.get_port(), '/', credentials)
        connection = BlockingConnection(parameters)
        self.__logger.debug("AMQP connection created")
        return connection

    def __create_channel(self):
        """
        A private method that creates the AMQP channel object.

        Returns:
            BlockingConnection.channel: The AMQP channel object.
        """
        self.__logger.debug("Creating AMQP channel")
        if self.__connection is None:
            self.__connection = self.__create_connection()
        channel = self.__connection.channel()
        self.__logger.debug("AMQP channel created")
        return channel

    def __init_queue(self):
        """
        A private method that initializes the AMQP queue.
        """
        self.__logger.debug("Initializing AMQP queues")
        self.__channel.queue_declare(
            queue=self.__config.get_livestream_pipeline_queue(), durable=True)
        self.__channel
        self.__logger.debug("AMQP queues initialized")

    def __close_channel(self):
        """
        A private method that closes the AMQP channel object.
        """
        self.__logger.debug("Closing AMQP channel")
        if self.__channel is not None:
            self.__channel.close()
            self.__channel = None
        self.__logger.debug("AMQP channel closed")

    def __close_connection(self):
        """
        A private method that closes the AMQP connection object.
        """
        self.__logger.debug("Closing AMQP connection")
        if self.__connection is not None:
            self.__connection.close()
            self.__connection = None
        self.__logger.debug("AMQP connection closed")

    def __on_pipeline_message(self, channel, method, properties, body):
        """
        A private method that handles the AMQP message consumption.

        Args:
            channel (BlockingConnection.channel): The AMQP channel object.
            method (pika.spec.Basic.Deliver): The AMQP delivery method.
            properties (pika.spec.BasicProperties): The AMQP message properties.
            body (bytes): The AMQP message body.
        """
        pipeline_request = Pipeline.StartPipelineRequest()
        pipeline_request.ParseFromString(body)
        self.__logger.debug("AMQP message received")
        self.__logger.debug("AMQP message body",
                            pipeline_request=pipeline_request)
        self.__logger.debug("AMQP message properties", properties=properties)
        self.__logger.debug("AMQP message method", method=method)
        self.__logger.debug("AMQP message channel", channel=channel)
