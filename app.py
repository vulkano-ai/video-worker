from signal import signal, SIGTERM, SIGINT
from threading import Event
from lib import Logger, ConfigManager, GstWorker, AmqpWorker
from prometheus_client import start_http_server as start_prometheus_server


class LivestreamAiService:
    def __init__(self):
        self.__health_check_worker = None
        self.__gst_worker = None
        self.__amqp_worker = None
        self.__close_event = Event()
        self.__logger = Logger().get_logger("Main thread")

    def main(self):
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
        self.__gst_worker = GstWorker.GstThread()
        self.__gst_worker.start()

        self.__amqp_worker = AmqpWorker.AmqpThread()
        self.__amqp_worker.start()
        return

    def stop_workers(self):
        self.__logger.info("Stopping workers")
        if self.__gst_worker is not None and self.__gst_worker.is_alive():
            self.__gst_worker.stop()
            self.__gst_worker.join()
            self.__logger.info("Gst worker closed")
        if self.__amqp_worker is not None and self.__amqp_worker.is_alive():
            self.__amqp_worker.stop()
            self.__amqp_worker.join()
            self.__logger.info("Amqp worker closed")
        return

    def quit(self):
        self.__logger.info("Closing...")
        self.__close_event.set()
        self.stop_workers()
        self.__logger.info("All workers stopped")
        # logger.info(self.__context__.destroy())
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
