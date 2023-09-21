from lib import Logger, ConfigManager
from inference import pipeline
import logging
from multiprocessing import Process
from ..processing.gstreamer import GstPipelineRunner


class GstProcess(Process):

    def __init__(self, config=None, default_sleep=1):
        super(GstProcess, self).__init__()
        self.logger = Logger().get_logger("Gst thread")
        self.config_manager = ConfigManager()

        self.logger.debug("GST thread init", config=config,
                          default_sleep=default_sleep)
        self.__default_sleep = default_sleep
        self.__runner = GstPipelineRunner(error_callback=self.__on_error_callback, eos_callback=self.__on_eos_callback)

    def __on_error_callback(self):
        # TODO handle error or abort
        self.__runner.stop_pipeline()
        pass

    def __on_eos_callback(self):
        # TODO handle eos
        self.__runner.stop_pipeline()
        pass

    def run(self):
        self.logger.debug("Gst thread running")
        self.logger.info("Starting Gst Pipeline")
        try:
            # The code will block here due to mainloop execution. We need a while loop only if we plan to reuse one
            # worker after a pipeline is completed.
            self.__runner.run_blocking()

        except Exception as e:
            self.logger.error("Gst error {}".format(e))
            self.stop()

        self.logger.debug("Gst thread closed")

    def stop(self):
        self.__runner.stop_pipeline()
