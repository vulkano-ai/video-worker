from prometheus_client import Summary, Counter, Gauge

VIDEO_PIPELINE_TIME = Summary('gst_pipeline_processing_seconds', 'Time spent by the video pipeline')

frame_processed = Counter('frame_processed', 'Number of frames processed')

concurrent_streams = Gauge('concurrent_streams', 'Number of concurrent streams')
