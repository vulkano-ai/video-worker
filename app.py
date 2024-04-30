from signal import signal, SIGTERM, SIGINT
from threading import Event
from lib import Logger, ConfigManager, AmqpWorker, PipelineWorker
from prometheus_client import start_http_server as start_prometheus_server
import queue
import gi
gi.require_version('Gst', '1.0')


class LivestreamAiService:
    """
    A class representing the Livestream AI service.

    Attributes:
    __health_check_worker: None
    __pipeline_worker: None
    __amqp_worker: None
    __close_event: threading.Event
    __logger: logging.Logger
    __job_queue: queue.Queue

    Methods:
    main: The main method of the service.
    start_workers: Starts the workers.
    stop_workers: Stops the workers.
    quit: Quits the service.
    """

    def __init__(self):
        """
        Initializes the LivestreamAiService class.
        """
        self.__health_check_worker = None
        self.__pipeline_worker = None
        self.__amqp_worker = None
        self.__close_event = Event()
        self.__logger = Logger().get_logger("Main thread")
        self.__job_queue = queue.Queue()

    def main(self):
        """
        The main method of the service.
        """
        self.__logger.info("Creating workers")
        self.start_workers()
        self.__logger.info("Workers created, waiting tread join")

        while not self.__close_event.is_set():
            self.__close_event.wait(timeout=1)
            # check workers status

            if self.__close_event.is_set():
                self.__logger.info("Stop")
                self.stop_workers()
                self.__logger.info("Workers exited")
                self.__close_event.wait(1)
                self.__logger.info("After wait")

    def start_workers(self):
        """
        Starts the workers.
        """
        self.__pipeline_worker = PipelineWorker.PipelineThread(
            queue=self.__job_queue)
        self.__pipeline_worker.start()

        self.__amqp_worker = AmqpWorker.AmqpThread(queue=self.__job_queue)
        self.__amqp_worker.start()
        return

    def stop_workers(self):
        """
        Stops the workers.
        """
        self.__logger.info("Stopping workers")
        # Amqp worker
        if self.__amqp_worker is not None and self.__amqp_worker.is_alive():
            self.__logger.debug("Stopping amqp worker")
            self.__amqp_worker.stop()
            self.__amqp_worker.join()
            self.__logger.info("Amqp worker closed")

        # Pipeline worker
        if self.__pipeline_worker is not None and self.__pipeline_worker.is_alive():
            self.__logger.debug("Stopping pipeline worker")
            self.__pipeline_worker.stop()
            self.__pipeline_worker.join()
            self.__logger.info("Pipeline worker closed")

        # Queue
        self.__logger.debug("Stopping queue")
        self.__logger.debug("Queue size: {}".format(self.__job_queue.qsize()))
        self.__job_queue.join()
        self.__logger.info("Queue closed")
        return

    def quit(self):
        """
        Quits the service.
        """
        self.__logger.info("Closing...")
        self.__close_event.set()
        self.__logger.info("All workers stopped")
        self.__logger.info("All resources destroyed")


if __name__ == '__main__':

    cfg = ConfigManager()
    logger = Logger().get_logger()

    def term_handler(sig, frame):
        logger.info("Quitting...")
        service.quit()
        logger.info("Done, exiting!")

    signal(SIGTERM, term_handler)
    signal(SIGINT, term_handler)

    logger.info("Starting prometheus server at port {}".format(
        cfg.get_metrics_port()))
    start_prometheus_server(cfg.get_metrics_port())

    logger.info("Starting detector service")
    service = LivestreamAiService()
    service.main()
