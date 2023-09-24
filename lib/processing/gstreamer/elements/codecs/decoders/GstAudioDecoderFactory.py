from common import Logger


class GstAudioDecoderFactory(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GstAudioDecoderFactory, cls).__new__(cls)
            cls._instance.__logger = Logger().get_logger("GstAudioDecoderFactory")
            cls._instance.__logger.debug("Creating GstAudioDecoderFactory")

    def create_audio_decoder(self, pad):
        self.__logger.debug("Creating Audio decoder")
        caps = pad.query_caps(None)
        name = caps.to_string()
        self.__logger.debug("Pad name: {}".format(name))

        pass
