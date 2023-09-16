from abc import abstractmethod


class GstPipelineOutput(object):

    def __init__(self, pipeline):
        self.pipeline = pipeline

    @abstractmethod
    def get_output_name(self) -> str:
        pass
