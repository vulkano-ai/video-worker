from signal import signal, SIGTERM, SIGINT
from threading import Event
from lib import Logger, ConfigManager
from lib.workers import GstWorker
from prometheus_client import start_http_server as start_prometheus_server

class LivestreamAiService:
	def __init__(self):
		self.__gst_worker__ = None
		self.__health_check_worker__ = None
		self.__close_event__ = Event()
		self.logger = Logger().get_logger("DetectorService")
		self.__gst_worker__ = None
		
	def main(self):
		while not self.__close_event__.is_set():
			self.logger.info("Creating workers")
			self.start_workers()
			self.logger.info("Workers created, waiting tread join")
			self.__gst_worker__.join()
			if not self.__close_event__.is_set():
				self.logger.info("Stop")
				self.stop_workers()
				self.logger.info("Workers exited")
				self.__close_event__.wait(1)
				self.logger.info("After wait")

	def start_workers(self):
		self.__gst_worker__ = GstWorker.GstThread()
		self.__gst_worker__.start()
		return

	def stop_workers(self):
		self.logger.info("Stopping workers")
		if self.__gst_worker__ is not None and self.__gst_worker__.is_alive():
			self.__gst_worker__.stop()
			self.__gst_worker__.join()
			self.logger.info("Gst worker closed")
		return

	def quit(self):
		self.logger.info("Closing...")
		self.__close_event__.set()
		self.stop_workers()
		self.logger.info("All workers stopped")
		# logger.info(self.__context__.destroy())
		self.logger.info("All resources destroyed")


if __name__ == '__main__':
	
	cfg = ConfigManager()
	logger = Logger().get_logger()

	def term_handler(sig, frame):
		logger.info("Quitting...")
		service.quit()
		logger.info("Done, exiting!")

	signal(SIGTERM, term_handler)
	signal(SIGINT, term_handler)

	logger.info("Starting prometheus server at port {}".format(cfg.get_metrics_port()))
	start_prometheus_server(cfg.get_metrics_port())

	logger.info("Starting detector service")
	service = DetectorService()
	service.main()
