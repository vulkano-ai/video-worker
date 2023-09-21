from lib import Logger
from lib.processing.gstreamer.utils.gst_utils import make_gst_element
from gi.repository import Gst
import os
import pyds
from .GstBaseVideoInfer import GstBaseVideoInfer
from edge.detector.detector_pb2 import DetectionOutput, ObjMeta, ClassifierMeta, LabelInfo
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime


class DetectionInfer(GstBaseVideoInfer):
    __muxer_output_width = 1920
    __muxer_output_height = 1080
    __muxer_batch_size = 1
    __muxer_batch_timeout_usec = 4000000
    __gpu_id = 0
    __pgie = None
    __num_sources = 2
    __verbose = True
    __muxer = None
    __demuxer = None
    __streams = []

    # PGIE config file path
    __confing_infer_primary_path__ = os.path.abspath(
        "./configs/config_infer_primary.txt")

    def __init__(self, pipeline, elem_id, src_video_tees, streams, gie="nvinfer", live_source=1):
        super().__init__(pipeline=pipeline, elem_id=elem_id, src_video_tees=src_video_tees)
        self.__logger = Logger().get_logger("DetectionInfer")
        self.__gie = gie
        self.__live_source = live_source
        self.__streams = streams

    def __create_muxer(self):
        self.__logger.debug("Creating muxer")
        self.__muxer = make_gst_element(
            "nvstreammux", "nvstreammux", "nvstreammux")

        self.get_pipeline().add(self.__muxer)
        # Default is live stream
        self.__muxer.set_property('live-source', self.__live_source)

        # Set muxer properties
        self.__logger.debug('Setting muxer properties')
        self.__muxer.set_property("width", self.__muxer_output_width)
        self.__muxer.set_property("height", self.__muxer_output_height)
        self.__muxer.set_property("batch-size", self.__muxer_batch_size)
        self.__muxer.set_property(
            "batched-push-timeout", self.__muxer_batch_timeout_usec)
        self.__muxer.set_property("gpu_id", self.__gpu_id)

        self.__logger.debug("Muxer created")

    def __configure_pgie(self):
        self.__pgie = make_gst_element('nvinfer', 'nvinfer', 'nvinfer')
        self.__pgie.set_property(
            "config-file-path", self.__confing_infer_primary_path__)

        # Manage Batch size
        pgie_batch_size = self.__pgie.get_property("batch-size")
        if pgie_batch_size < self.__num_sources:
            self.__logger.warning(
                "Overriding infer-config batch-size {} with number of sources {} \n".format(pgie_batch_size,
                                                                                            self.__num_sources))
            pgie_batch_size = self.__num_sources
        self.__pgie.set_property("batch-size", pgie_batch_size)

        self.get_pipeline().add(self.__pgie)

        pgiesrcpad = self.__pgie.get_static_pad("src")
        if not pgiesrcpad:
            self.__logger.error(" Unable to get src pad of primary infer")
            raise TypeError("Unable to get src pad of primary infer")

        pgiesrcpad.add_probe(Gst.PadProbeType.BUFFER, self.__on_pgie_data, 0)

    def __on_pgie_data(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            self.__logger.error("Unable to get GstBuffer ")
            return

        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as inputs, which is obtained with hash(gst_buffer)
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        l_frame = batch_meta.frame_meta_list
        while l_frame is not None:
            try:
                # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
                # The casting is done by pyds.NvDsFrameMeta.cast()
                # The casting also keeps ownership of the underlying memory
                # in the C code, so the Python garbage collector will leave
                # it alone.
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration:
                break

            frame_number = frame_meta.frame_num
            l_obj = frame_meta.obj_meta_list
            num_rects = frame_meta.num_obj_meta

            # Check if infer has been done on frame
            if frame_meta.bInferDone is not None:
                output_detection = DetectionOutput()

                # output_detection.metadata =
                output_detection.num_objects = num_rects
                output_detection.frame_number = frame_number
                output_detection.source_frame_width = frame_meta.source_frame_width
                output_detection.source_frame_height = frame_meta.source_frame_height
                # Creating and setting timestamp
                t = datetime.now().timestamp()
                seconds = int(t)
                nanos = int(t % 1 * 1e9)
                output_detection.timestamp.seconds = seconds
                output_detection.timestamp.nanos = nanos

                output_detection.metadata.CopyFrom(
                    self.__streams[frame_meta.batch_id].metadata)

                while l_obj is not None:
                    try:
                        # Casting l_obj.data to pyds.NvDsObjectMeta
                        obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

                        obj_meta_proto = ObjMeta()

                        obj_meta_proto.class_id = obj_meta.class_id
                        obj_meta_proto.obj_label = obj_meta.obj_label
                        obj_meta_proto.confidence = obj_meta.confidence
                        # Bounding Box infos
                        obj_meta_proto.bounding_box.left = obj_meta.rect_params.left
                        obj_meta_proto.bounding_box.top = obj_meta.rect_params.top
                        obj_meta_proto.bounding_box.height = obj_meta.rect_params.height
                        obj_meta_proto.bounding_box.width = obj_meta.rect_params.width

                        output_detection.obj_meta.append(obj_meta_proto)

                        # Per aggiungere informazioni utente alla frame da passare al prossimo prob, seguire:
                        #   https://docs.nvidia.com/metropolis/deepstream/python-api/PYTHON_API/NvDsMeta/NvDsUserMeta.html#pyds.NvDsUserMeta

                        if obj_meta.classifier_meta_list is not None:
                            for meta in obj_meta.classifier_meta_list:
                                classifier_meta_proto = ClassifierMeta()

                                classifier_meta_proto.num_labels = meta.num_labels
                                classifier_meta_proto.unique_component_id = meta.unique_component_id

                                if meta.label_info_list is not None:
                                    for label_info in meta.label_info_list:
                                        label_info_proto = LabelInfo()
                                        label_info_proto.num_classes = label_info.num_classes
                                        label_info_proto.result_label = label_info.result_label
                                        label_info_proto.pResult_label = label_info.pResult_label
                                        label_info_proto.result_class_id = label_info.result_class_id
                                        label_info_proto.label_id = label_info.label_id
                                        label_info_proto.result_prob = label_info.result_prob

                                        classifier_meta_proto.label_info.append(
                                            label_info_proto)

                                output_detection.obj_meta.classifier_meta_list.append(
                                    classifier_meta_proto)

                    except StopIteration:
                        break
                    try:
                        l_obj = l_obj.next
                    except StopIteration:
                        break
                self.__logger.info("output_detection",
                                   output_detection=output_detection)
            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK

    def __create_demuxer(self):
        self.__logger.debug("Creating Demuxer")
        self.__demuxer = make_gst_element(
            "nvstreamdemux", "nvstreamdemux", "nvstreamdemux")
        self.get_pipeline().add(self.__demuxer)

    def __create_queue(self, idx):
        queue = make_gst_element('queue', "queue_tee_%u" %
                                 idx, "queue_tee_%u" % idx)
        self.get_pipeline().add(queue)
        return queue

    def __link_input_tee(self, idx):
        self.__logger.debug('Linking input tee with queue')
        input_tee = self._src_video_tees[idx]
        queue_src = self.__create_queue(idx)
        input_tee.link(queue_src)
        queue_src_pad = queue_src.get_static_pad("src")
        muxer_sink_pad = self.__muxer.get_request_pad("sink_%u" % idx)
        if not muxer_sink_pad:
            self.__logger.error("Unable to create sink pad bin\n")
        queue_src_pad.link(muxer_sink_pad)
        self.__logger.debug('Linked input tee')

    def __link_output_tee(self, idx):
        self.__logger.debug('Linking demux with output tee')
        out_tee = self._out_video_tees[idx]
        demux_src_pad = self.__demuxer.get_request_pad("src_%u" % idx)
        if not demux_src_pad:
            self.__logger.error('Unable to get the src pad of streamdemux')

        tee_out_sink_pad = out_tee.get_static_pad("sink")
        if not tee_out_sink_pad:
            self.__logger.error("Unable to get the sink pad of tee")

        demux_src_pad.link(tee_out_sink_pad)
        self.__logger.debug('Linked output tee')

    def build_video_infer(self):
        self.__create_muxer()
        self.__configure_pgie()
        self.__create_demuxer()

        for tee_id in range(len(self._src_video_tees)):
            self.__link_input_tee(tee_id)

        self.__muxer.link(self.__pgie)
        self.__pgie.link(self.__demuxer)

        for tee_id in range(len(self._out_video_tees)):
            self.__link_output_tee(tee_id)
