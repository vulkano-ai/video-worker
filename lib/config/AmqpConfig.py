import os
from ..common.Logger import Logger


class AmqpConfig:
    """
    A class used to represent the AMQP configuration.

    ...

    Attributes
    ----------
    __host : str
        the AMQP host
    __port : int
        the AMQP port
    __username : str
        the AMQP username
    __password : str
        the AMQP password
    __livestream_pipeline_queue : str
        the name of the queue for the livestream pipeline
    __logger : Logger
        the logger for the class

    Methods
    -------
    get_host()
        Returns the AMQP host.
    get_port()
        Returns the AMQP port.
    get_username()
        Returns the AMQP username.
    get_password()
        Returns the AMQP password.
    get_livestream_pipeline_queue()
        Returns the name of the queue for the livestream pipeline.
    get_connection_string()
        Returns the connection string for the AMQP server.
    """

    __host = None
    __port = None
    __username = None
    __password = None
    __livestream_pipeline_queue = None
    __logger = Logger().get_logger("AmqpConfig")

    def __init__(self) -> None:
        """
        Constructs all the necessary attributes for the AMQP configuration object.
        """
        self.__host = os.getenv("AMQP_HOST", "localhost")
        self.__port = os.getenv("AMQP_PORT", 5672)
        self.__username = os.getenv("AMQP_USERNAME", "user")
        self.__password = os.getenv("AMQP_PASSWORD", "password")
        self.__livestream_pipeline_queue = os.getenv(
            "LIVESTREAM_PIPELINE_QUEUE", "pipelines")
        self.__logger.debug("AmqpConfig init completed",
                            host=self.__host,
                            port=self.__port,
                            livestream_pipeline_queue=self.__livestream_pipeline_queue
                            )

    def get_host(self):
        """
        Returns the AMQP host.

        Returns
        -------
        str
            the AMQP host
        """
        return self.__host

    def get_port(self):
        """
        Returns the AMQP port.

        Returns
        -------
        int
            the AMQP port
        """
        return self.__port

    def get_username(self):
        """
        Returns the AMQP username.

        Returns
        -------
        str
            the AMQP username
        """
        return self.__username

    def get_password(self):
        """
        Returns the AMQP password.

        Returns
        -------
        str
            the AMQP password
        """
        return self.__password

    def get_livestream_pipeline_queue(self):
        """
        Returns the name of the queue for the livestream pipeline.

        Returns
        -------
        str
            the name of the queue for the livestream pipeline
        """
        return self.__livestream_pipeline_queue

    def get_connection_string(self):
        """
        Returns the connection string for the AMQP server.

        Returns
        -------
        str
            the connection string for the AMQP server
        """
        return f"amqp://{self.__username}:{self.__password}@{self.__host}:{self.__port}"
