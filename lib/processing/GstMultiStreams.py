import gi
import pyds
import os
from edge.detector.detector_pb2 import VideoCodec

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GObject, Gst, GstRtspServer, GLib
from lib.common.is_aarch_64 import is_aarch64
from lib.common.bus_call import bus_call
# from lib.common import Runner
from lib import Logger

MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_SIZE = 1
MUXER_BATCH_TIMEOUT_USEC = 4000000
OUTPUT_BITRATE = 4000000
RTSP_PORT_NUM = 8885

GPU_ID = 0


class Stream:
    uri = None
    codec = 'H264'
    bitrate = 4000000


class GstMultiStreamsClass:

    def __init__(self, streams: [Stream], verbose=False, error_callback=None,
                 config_file_path="./configs/detection_nvinfer.txt"):
        super(GstMultiStreamsClass)
        self.__logger__ = Logger().get_logger("GstMultiStreamsClass")
        self.__streams__ = self.__manage_stream__(streams)
        self.__gie__ = "nvinfer"
        self.__is_live__ = True  # Default true because streams are rtsp
        self.__num_sources__ = len(self.__streams__)

        self.__muxer__ = None
        self.__pgie__ = None
        self.__demuxer__ = None

        # PGIE config file path
        self.__confing_infer_primary_path__ = os.path.abspath(config_file_path)

        # Standard GStreamer initialization
        self.__init_gst__()

        # Pipeline initialization
        self.__pipeline__ = self.__init_pipeline__()

        self.__loop__ = GLib.MainLoop()

        self.verbose = verbose

        self.error_callback = error_callback or self.quit

    def __manage_stream__(self, streams):
        if streams is None:
            raise ValueError('No streams found')
        return streams if isinstance(streams, list) else [streams]

    def __is_valid_codec__(self, codec):
        if codec in ['H264', 'H265']:
            return codec
        else:
            raise ValueError("RTSP Streaming Codec must be on of H264/H265")

    def __init_gst__(self):
        self.__logger__.debug("Standard GStreamer initialization")
        GObject.threads_init()
        Gst.init(None)

    def __init_pipeline__(self):
        self.__logger__.debug("Creation pipeline")
        pipeline = Gst.Pipeline()
        if not pipeline:
            raise ValueError(" Unable to create Pipeline \n")
        return pipeline

    def __make_element__(self, factoryname, name, printedname, detail=""):
        """ Creates an element with Gst Element Factory make.
            Return the element  if successfully created, otherwise print
            to stderr and return None.
        """
        self.__logger__.debug("Creating element {}, {}".format(name, factoryname))
        elm = Gst.ElementFactory.make(factoryname, name)
        if not elm:
            self.__logger__.error("Unable to create " + printedname + " \n")
            if detail:
                self.__logger__.error(detail=detail)
        return elm

    def __configure_inputs__(self):
        # Create nvstreammux instance to form batches from one or more sources.
        self.__logger__.debug('Creating muxer...')
        self.__muxer__ = self.__make_element__("nvstreammux", "Stream-muxer", "NvStreamMux")

        self.__logger__.debug('Muxer created, adding to pipeline...')
        self.__pipeline__.add(self.__muxer__)

        for idx in range(self.__num_sources__):
            source_uri = self.__streams__[idx].uri
            self.__configure_source__(idx, source_uri)

        self.__configure_muxer__()

    def __configure_source__(self, idx, uri):
        '''
        Configure sources function, create a source bin and connect it to streammux pad
        :param idx:
        :param uri:
        :return:
        '''
        self.__logger__.debug("Creating rtspsrc #{}".format(idx))

        rtspsrc = self.__make_element__("rtspsrc", "rtspsrc-%02d" % idx, "rtspsrc")
        depay = self.__make_element__("rtph264depay", "rtspdepay-%02d" % idx, "rtph264depay")
        parse = self.__make_element__("h264parse", "rtspparse-%02d" % idx, "h264parse")
        decoder = self.__make_element__("nvv4l2decoder", "rtspdecoder-%02d" % idx, "nvv4l2decoder")
        nvvidconv = self.__make_element__("nvvideoconvert", "rtspconvertor-%02d" % idx, "nvvidconv")
        caps = self.__make_element__("capsfilter", "rtspfilter-%02d" % idx, "capsfilter")

        streammux_sink_pad = self.__muxer__.get_request_pad("sink_%u" % idx)
        if not streammux_sink_pad:
            self.__logger__.error("Unable to create sink pad bin\n")

        self.__pipeline__.add(rtspsrc)
        self.__pipeline__.add(depay)
        self.__pipeline__.add(parse)
        self.__pipeline__.add(decoder)
        self.__pipeline__.add(nvvidconv)

        rtspsrc.set_property('location', uri)
        rtspsrc.set_property('latency', 0)
        rtspsrc.set_property('drop-on-latency', True)
        rtspsrc.set_property('buffer-mode', 0)
        rtspsrc.set_property('do-retransmission', False)
        rtspsrc.set_property('timeout', 0)
        rtspsrc.set_property('retry', 0)

        # rtspsrc.link(depay)
        depay.link(parse)
        parse.link(decoder)
        decoder.link(nvvidconv)
        nvvidconv.link(self.__muxer__)


        rtspsrc.connect("pad-added", self.__new_rtsp_pad_added__, nvvidconv)
        # # Create first source bin and add to pipeline
        # bin_name = "source-bin-%02d" % idx
        #
        # source_bin = self.__create_source_bin__(bin_name, uri)
        # if not source_bin:
        #     self.__logger__.error("Failed to create source bin. Exiting... \n")
        #     raise ValueError("Failed to create source bin.")
        #
        # self.__pipeline__.add(source_bin)
        #
        # # Create pad
        # padname = "sink_%u" % idx
        #
        # sinkpad = self.__muxer__.get_request_pad(padname)
        # if not sinkpad:
        #     self.__logger__.error("Unable to create sink pad bin\n")
        #
        # srcpad = source_bin.get_static_pad("src")
        # if not srcpad:
        #     self.__logger__.error("Unable to create src pad bin\n")
        #
        # srcpad.link(sinkpad)

    def __new_rtsp_pad_added__(self, element, pad, nvvidconv):

        self.__logger__.debug("In cb_new_rtspsrc_pad_added\n")
        new_pad_caps = pad.query_caps(None)
        new_pad_name = new_pad_caps.get_structure(0).get_name()
        self.__logger__.debug("new_pad_name", new_pad_name=new_pad_name)
        if new_pad_name.startswith("video/x-raw"):
            sink_pad = self.__muxer__.get_static_pad("sink")
            if not sink_pad.is_linked():
                pad.link(sink_pad)
                print("Pad added and linked:", pad.get_name())


    def __create_source_bin__(self, bin_name, uri):
        self.__logger__.debug("Creating source bin")

        # Create a source GstBin to abstractsource_id this bin's content from the rest of the pipeline
        nbin = Gst.Bin.new(bin_name)
        if not nbin:
            self.__logger__.error(" Unable to create source bin \n")

        # Source element for reading from the uri.
        # We will use decodebin and let it figure out the container format of the
        # stream and the codec and plug the appropriate demux and decode plugins.
        uri_decode_bin = self.__make_element__("uridecodebin", "uri-decode-bin", 'uri-decode-bin')

        # We set the inputs uri to the source element
        uri_decode_bin.set_property("uri", uri)
        # Connect to the "pad-added" signal of the decodebin which generates a
        # callback once a new pad for raw data has beed created by the decodebin
        pad_int = uri_decode_bin.connect("pad-added", self.__cb_newpad__, nbin)
        self.__logger__.debug('Connected uri_decode_bin, with pad: {}'.format(pad_int))
        child_int = uri_decode_bin.connect("child-added", self.__decodebin_child_added__, nbin)
        self.__logger__.debug('Connected uri_decode_bin, with child: {}'.format(child_int))

        # We need to create a ghost pad for the source bin which will act as a proxy
        # for the video decoder src pad. The ghost pad will not have a target right
        # now. Once the decode bin creates the video decoder and generates the
        # cb_newpad callback, we will set the ghost pad target to the video decoder
        # src pad.
        Gst.Bin.add(nbin, uri_decode_bin)

        # uri_decode_bin.disconnect(pad_int)
        # uri_decode_bin.disconnect(child_int)

        bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
        if not bin_pad:
            self.__logger__.error(" Failed to add ghost pad in source bin \n")
            return None
        return nbin

    def __cb_newpad__(self, decodebin, decoder_src_pad, data):
        self.__logger__.debug("In cb_newpad\n")
        caps = decoder_src_pad.get_current_caps()
        gststruct = caps.get_structure(0)
        gstname = gststruct.get_name()
        source_bin = data
        features = caps.get_features(0)

        # Need to check if the pad created by the decodebin is for video and not audio.
        self.__logger__.debug("gstname", gstname=gstname)
        if gstname.find("video") != -1:
            # Link the decodebin pad only if decodebin has picked nvidia
            # decoder plugin nvdec_*. We do this by checking if the pad caps contain
            # NVMM memory features.
            self.__logger__.debug("features ", features=features)
            if features.contains("memory:NVMM"):
                # Get the source bin ghost pad
                bin_ghost_pad = source_bin.get_static_pad("src")
                if not bin_ghost_pad.set_target(decoder_src_pad):
                    self.__logger__.error("Failed to link decoder src pad to source bin ghost pad\n")
            else:
                self.__logger__.error(" Error: Decodebin did not pick nvidia decoder plugin.\n")

    def __decodebin_child_added__(self, child_proxy, Object, name, user_data):
        self.__logger__.debug("Decodebin child added: {}".format(name))
        if name.find("decodebin") != -1:
            Object.connect("child-added", self.__decodebin_child_added__, user_data)
        if is_aarch64() and name.find("nvv4l2decoder") != -1:
            self.__logger__.debug("Seting bufapi_version\n")
            Object.set_property("bufapi-version", True)

    def __configure_muxer__(self):
        self.__muxer__.set_property('live-source', 1)

        self.__muxer__.set_property("width", MUXER_OUTPUT_WIDTH)
        self.__muxer__.set_property("height", MUXER_OUTPUT_HEIGHT)
        self.__muxer__.set_property("batch-size", MUXER_BATCH_SIZE)
        self.__muxer__.set_property("batched-push-timeout", MUXER_BATCH_TIMEOUT_USEC)
        self.__muxer__.set_property("gpu_id", GPU_ID)

    def __configure_pgie__(self):
        self.__pgie__ = self.__make_element__("nvinfer", "primary-inference", "Pgie")
        self.__pgie__.set_property("config-file-path", self.__confing_infer_primary_path__)

        # Manage Batch size
        pgie_batch_size = self.__pgie__.get_property("batch-size")
        if pgie_batch_size < self.__num_sources__:
            self.__logger__.warning(
                "Overriding infer-config batch-size {} with number of sources {} \n".format(pgie_batch_size,
                                                                                            self.__num_sources__))
            pgie_batch_size = self.__num_sources__
        self.__pgie__.set_property("batch-size", pgie_batch_size)

        self.__pipeline__.add(self.__pgie__)

        pgiesrcpad = self.__pgie__.get_static_pad("src")
        if not pgiesrcpad:
            self.__logger__.error(" Unable to get src pad of primary infer")

        pgiesrcpad.add_probe(Gst.PadProbeType.BUFFER, self.__on_pgie_data__, 0)

        self.__logger__.debug("Creating/Adding Queue between muxer and pgie...")
        queue_pgie = self.__make_element__('queue', "pgie_queue", "pgie_queue")
        self.__pipeline__.add(queue_pgie)
        # Link queue_pgie between muxer and pgie...
        self.__muxer__.link(queue_pgie)
        queue_pgie.link(self.__pgie__)

        # self.__muxer__.link(self.__pgie__)

    def __on_pgie_data__(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            self.__logger__.error("Unable to get GstBuffer ")
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

            if self.verbose:
                print("---------------------  Frame Properties  -----------------------------")
                print("n_frame:", frame_number)
                print("n_object:", num_rects)
                print("frame_meta.bInferDone:", frame_meta.bInferDone)
                print("frame_meta.batch_id:", frame_meta.batch_id)
                print("frame_meta.ntp_timestamp:", frame_meta.ntp_timestamp)
                print("frame_meta.source_frame_width:", frame_meta.source_frame_width)
                print("frame_meta.source_frame_height:", frame_meta.source_frame_height)

            while l_obj is not None:
                try:
                    # Casting l_obj.data to pyds.NvDsObjectMeta
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                    if self.verbose:
                        print("-------------- Object Properties: ")
                        print("=> unique_component_id:", obj_meta.unique_component_id)
                        print("=> object_id:", obj_meta.object_id)
                        print("=> class_id:", obj_meta.class_id)
                        print("=> confidence:", obj_meta.confidence)
                        print("=> obj_meta.detector_bbox_info",
                              obj_meta.detector_bbox_info.org_bbox_coords.left,
                              obj_meta.detector_bbox_info.org_bbox_coords.top,
                              obj_meta.detector_bbox_info.org_bbox_coords.width,
                              obj_meta.detector_bbox_info.org_bbox_coords.height
                              )
                        print("=> obj_meta.rect_params",
                              obj_meta.rect_params.left,
                              obj_meta.rect_params.top,
                              obj_meta.rect_params.width,
                              obj_meta.rect_params.height,
                              obj_meta.rect_params.border_width,
                              ", obj_meta.rect_params.colors",
                              obj_meta.rect_params.border_color.red,
                              obj_meta.rect_params.border_color.green,
                              obj_meta.rect_params.border_color.blue,
                              obj_meta.rect_params.border_color.alpha,
                              ", obj_meta.rect_params.has_bg_color",
                              obj_meta.rect_params.has_bg_color,
                              ", obj_meta.rect_params.has_color_info",
                              obj_meta.rect_params.has_color_info,

                              )
                        print("----------------------------------")
                except StopIteration:
                    break
                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break

            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK

    def build_pipeline(self):
        self.__configure_inputs__()
        self.__configure_pgie__()
        self.__configure_outputs__()

    def __configure_outputs__(self):
        self.__configure_rtsp_sink__()

    def __configure_fake_sink__(self):
        sink = self.__make_element__("fakesink", "sink", "Sink")
        self.__pipeline__.add(sink)
        self.__pgie__.link(sink)

    def __configure_rtsp_sink__(self):
        self.__demuxer__ = self.__make_element__("nvstreamdemux", "Stream-demuxer", "NvStreamdeMux")
        self.__pipeline__.add(self.__demuxer__)
        self.__pgie__.link(self.__demuxer__)

        rtsp_out_server = self.__start_rtsp_server__()

        for idx in range(self.__num_sources__):
            self.__configure_output__(idx, rtsp_out_server)

    def __configure_output__(self, source_id, server):
        # Create filter ekements
        nvvideoconvert = self.__make_element__("nvvideoconvert", "convertor%u" % source_id, "nvvidconv%u" % source_id)
        nvosd = self.__make_element__("nvdsosd", "onscreendisplay%u" % source_id, "nvdsosd%u" % source_id)
        nvvideoconvert_postosd = self.__make_element__("nvvideoconvert",
                                                       "convertor_postosd%u" % source_id,
                                                       "nvvideoconvert%u" % source_id)
        caps = self.__make_element__("capsfilter", "filter%u" % source_id, "filter%u" % source_id)
        encoder = self.__make_element__("nvv4l2h264enc", "encoder%u" % source_id,
                                        "Encoder%u" % source_id)
        rtppay = self.__make_element__("rtph264pay", "rtppay%u" % source_id, "RtpPay%u" % source_id)

        caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

        if not encoder:
            self.__logger__.error("Unable to create encoder")
        encoder.set_property("bitrate", OUTPUT_BITRATE)
        if is_aarch64():
            encoder.set_property("preset-level", 1)
            encoder.set_property('insert-sps-pps', 1)
            encoder.set_property('bufapi-version', 1)

        udpsink_port_num = 5500 + source_id
        sink = self.__make_element__("udpsink", "udpsink%u" % source_id, "Udpsink%u" % source_id)
        sink.set_property("host", "224.224.255.255")
        sink.set_property("port", udpsink_port_num)
        sink.set_property("async", False)
        sink.set_property("sync", 1)
        sink.set_property("qos", 0)

        queue_sink = self.__make_element__('queue', "queue_sink_%u" % source_id, "QueueSink%u" % source_id)

        self.__pipeline__.add(nvvideoconvert)
        self.__pipeline__.add(nvosd)
        self.__pipeline__.add(nvvideoconvert_postosd)
        self.__pipeline__.add(caps)
        self.__pipeline__.add(encoder)
        self.__pipeline__.add(rtppay)
        self.__pipeline__.add(queue_sink)
        self.__pipeline__.add(sink)

        self.__logger__.debug('Creating osdsinkpad ...')
        osdsinkpad = nvosd.get_static_pad("sink")
        if not osdsinkpad:
            self.__logger__.error("Unable to get sink pad of nvosd")
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self.__on_osd_data__, 0)

        self.__logger__.debug('Creating demux_src_pad ...')
        demux_src_pad = self.__demuxer__.get_request_pad("src_%u" % source_id)
        if not demux_src_pad:
            self.__logger__.error('Unable to get the src pad of streamdemux')
        self.__logger__.debug('Creating vc_sink_pad ...')
        vc_sink_pad = nvvideoconvert.get_static_pad("sink")
        if not vc_sink_pad:
            self.__logger__.error("Unable to get the sink pad of nvvidconv")

        self.__logger__.debug('Linking demux_src_pad with vc_sink_pad ...')
        demux_src_pad.link(vc_sink_pad)

        self.__logger__.debug('Linking Filters ...')
        nvvideoconvert.link(nvosd)
        nvosd.link(nvvideoconvert_postosd)
        nvvideoconvert_postosd.link(caps)
        caps.link(encoder)
        encoder.link(rtppay)
        rtppay.link(queue_sink)
        queue_sink.link(sink)

        factory = GstRtspServer.RTSPMediaFactory.new()
        factory.set_launch(
            "( udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (
                udpsink_port_num, VideoCodec.Name(self.__streams__[source_id].codec)))
        factory.set_shared(True)
        server.get_mount_points().add_factory("/streaming-%u" % source_id, factory)
        print(
            "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:{}/streaming-{} ***\n\n".format(
                RTSP_PORT_NUM, source_id)
        )

    def __on_osd_data__(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            self.__logger__.error("Unable to get GstBuffer ")
            return

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

            # Acquiring a display meta object. The memory ownership remains in
            # the C code so downstream plugins can still access it. Otherwise
            # the garbage collector will claim it when this probe function exits.
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_labels = 1
            py_nvosd_text_params = display_meta.text_params[0]
            # Setting display text to be shown on screen
            # Note that the pyds module allocates a buffer for the string, and the
            # memory will not be claimed by the garbage collector.
            # Reading the display_text field here will return the C address of the
            # allocated string. Use pyds.get_string() to get the string content.
            py_nvosd_text_params.display_text = "Frame Number={} \nNumber of Objects={}".format(
                frame_number,
                num_rects)

            # Now set the offsets where the string should appear
            py_nvosd_text_params.x_offset = 4
            py_nvosd_text_params.y_offset = 2

            # Font , font-color and font-size
            py_nvosd_text_params.font_params.font_name = "Serif"
            py_nvosd_text_params.font_params.font_size = 10
            # set(red, green, blue, alpha); set to White
            py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # Text background color
            py_nvosd_text_params.set_bg_clr = 1
            # set(red, green, blue, alpha); set to Black
            py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
            # Using pyds.get_string() to get display_text as string

            # print(pyds.get_string(py_nvosd_text_params.display_text))
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK

    def __start_rtsp_server__(self):
        server = GstRtspServer.RTSPServer.new()
        server.props.service = "%d" % RTSP_PORT_NUM
        server.attach(None)
        return server

    def start_pipeline(self):
        self.__configure__()
        self.set_playing()

        try:
            self.__loop__.run()
        # except KeyboardInterrupt:
        #     print('Terminated via Ctrl-C')
        except BaseException as e:
            print(e.__context__)
            pass

        self.set_null()

    def is_playing(self):
        return self.__pipeline__.get_state(Gst.CLOCK_TIME_NONE) == Gst.State.PLAYING

    def __configure__(self):
        self.__logger__.debug('configuring pipeline')

        bus = self.__pipeline__.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, self.__loop__)
        bus.connect("message::eos", self.__on_eos__)
        bus.connect("message::error", self.__on_error__)
        bus.connect("message::state-changed", self.__on_state_change__)

    def __on_eos__(self, _bus, message):
        self.__logger__.error("EOS from {} (at {})".format(
            message.src.name, message.src.get_path_string()))
        self.error_callback('EOS')

    def __on_error__(self, _bus, message):
        (error, debug) = message.parse_error()
        self.__logger__.error(
            "Error from {} (at {})\n{} ({})".format(message.src.name, message.src.get_path_string(), error, debug))
        self.error_callback("ERROR")

    def quit(self, *args):
        self.__logger__.warning('quitting mainloop')
        self.__loop__.quit()

    def __on_state_change__(self, _bus, message):
        old_state, new_state, pending = message.parse_state_changed()
        if message.src == self.__pipeline__:
            self.__logger__.info("Pipeline: State-Change from {} to {}; pending {}".format(
                old_state.value_name, new_state.value_name, pending.value_name))
        else:
            self.__logger__.debug("{}: State-Change from {} to {}; pending {}".format(
                message.src.name, old_state.value_name, new_state.value_name, pending.value_name))

    def set_playing(self):
        self.__logger__.info('requesting state-change to PLAYING')
        self.__pipeline__.set_state(Gst.State.PLAYING)

    def set_null(self):
        self.__logger__.info('requesting state-change to NULL')
        self.__pipeline__.set_state(Gst.State.NULL)

    def stop_pipeline(self):
        self.set_null()
        self.quit()
