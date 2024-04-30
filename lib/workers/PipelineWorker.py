from threading import Event, Thread
from lib import Logger, ConfigManager
from inference.pipeline.pipeline_pb2 import Pipeline, StartPipelineRequest
from queue import Queue
from .GstWorker import GstProcess
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
        # if we need to track the workers we can use a dictionary with and id.
        # It will be very useful for dispatching message to workers for changing the actual pipeline
        self.__active_workers = []

    def run(self):
        self.__logger.debug("Gst thread running")
        while not self.__close_event.is_set():
            try:
                if not self.__queue.empty():
                    self.__close_event.wait(self.__default_sleep * 10)
                    pipeline_request: StartPipelineRequest = self.__queue.get()
                    self.__logger.debug(
                        "Got job from queue: {}".format(pipeline_request))
                    # spawn new GstWorker process
                    self.__add_worker(
                        config=None, pipeline_request=pipeline_request)
                    self.__queue.task_done()
                else:
                    self.__close_event.wait(self.__default_sleep)

            except Exception as e:
                self.__logger.error("Gst error {}".format(e))
                self.stop()
        self.__logger.debug("Gst thread closed")

    def __add_worker(self, config, pipeline_request: StartPipelineRequest):
        new_worker = GstProcess(config=config,
                                default_sleep=self.__default_sleep,
                                pipeline_request=pipeline_request)
        new_worker.start()
        self.__logger.debug(
            "=================> New worker spawned: {}".format(new_worker))
        self.__active_workers.append(new_worker)
        self.__logger.debug("Active workers:",
                            active_workers=self.__active_workers)

    def __close_workers(self):
        self.__logger.debug("Closing workers", workers=self.__active_workers)
        for worker in self.__active_workers:

            worker.stop()
            # we wait 10 seconds for gracefully shutdown
            if worker.is_alive():
                worker.join(10)
                self.__logger.warning(
                    "Worker {} is still alive. Killing it.".format(worker))
                worker.kill()
        self.__active_workers = []

    def stop(self):
        self.__logger.info("Stopping pipeline thread")
        self.__close_workers()
        self.__close_event.set()
