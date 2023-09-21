from threading import Event, Thread
from lib import Logger, ConfigManager
from inference.pipeline import pipeline_pb2 as Pipeline
from queue import Queue

# process controller thread


class PipelineThread(Thread):

    def __init__(self, queue: Queue = None, default_sleep=1):
        super(PipelineThread, self).__init__()
        self.__logger = Logger().get_logger("Pipeline thread")
        self.__config_manager = ConfigManager()
        self.__queue = queue
        self.__logger.debug("Pipeline thread init",
                            default_sleep=default_sleep)

        self.__close_event = Event()
        self.__default_sleep = default_sleep

    def run(self):
        self.__logger.debug("Gst thread running")
        self.__logger.info("Starting Gst Pipeline")
        while not self.__close_event.is_set():
            try:
                if not self.__queue.empty():
                    pipeline: Pipeline = self.__queue.get()
                    self.__logger.debug(
                        "Got job from queue: {}".format(pipeline))
                    # spawn new GstWorker process
                    self.__queue.task_done()
                else:
                    self.__close_event.wait(self.__default_sleep)

            except Exception as e:
                self.logger.error("Gst error {}".format(e))
                self.stop()
        self.logger.debug("Gst thread closed")

    def stop(self):
        self.__close_event.set()
