from lib import Logger, ConfigManager
from inference import pipeline
import logging
from multiprocessing import Process
from ..processing.gstreamer.GstPipeline import GstPipeline
from inference.pipeline.pipeline_pb2 import Pipeline, StartPipelineRequest
import traceback

import gi
gi.require_version('Gst', '1.0')


class GstProcess(Process):

    def __init__(self, config=None, default_sleep=1, pipeline_request: StartPipelineRequest = None):
        super(GstProcess, self).__init__()
        self.__logger = Logger().get_logger("Gst thread")
        self.config_manager = ConfigManager()

        self.__logger.debug("GST thread init", config=config,
                            default_sleep=default_sleep)
        self.__default_sleep = default_sleep
        self.__runner = GstPipeline()
        self.__pipeline_request = pipeline_request

    def __on_error_callback(self):
        # TODO handle error or abort
        self.__runner.stop_pipeline()
        pass

    def __on_eos_callback(self):
        # TODO handle eos
        self.__runner.stop_pipeline()
        pass

    def run(self):
        self.__logger.debug("Gst thread running")
        self.__logger.info("Starting Gst Pipeline")
        try:
            # The code will block here due to mainloop execution. We need a while loop only if we plan to reuse one
            # worker after a pipeline is completed.
            self.__logger.debug("Creating livestream pipeline")
            self.__runner.create_livestream_pipeline(
                pipeline_request=self.__pipeline_request)
            self.__runner.run_blocking()
        except Exception as e:
            traceback.print_exc()
            self.__logger.error("Gst error {}".format(e))
            self.stop()

        self.__logger.debug("Gst thread closed")

    def stop(self):
        self.__logger.debug("Stopping Gst thread")
        self.__runner.stop_pipeline()

        self.__logger.debug("Gst thread stopped")
