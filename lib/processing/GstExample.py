import time
from lib import Logger, Metrics


class GstExampleClass:
    def __init__(self):
        super(GstExampleClass)
        self.logger = Logger().get_logger("GstExampleClass")

    @Metrics.VIDEO_PIPELINE_TIME.time()
    def do_something(self, message):
        self.logger.info("Received message")
        Metrics.frame_processed.inc()
        self.logger.info("Working")
        time.sleep(2)
        return message
