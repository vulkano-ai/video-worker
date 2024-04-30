FROM nvcr.io/nvidia/deepstream:6.3-gc-triton-devel as yolobuilder
RUN apt update && apt install -y git make

RUN apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl \
    gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo.git

RUN cd DeepStream-Yolo && CUDA_VER=12.1 make -C nvdsinfer_custom_impl_Yolo -j$(nproc)

RUN cp DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so /usr/local/lib/libnvdsinfer_yolo_v8.so  && \
    cd ../ && rm -rf DeepStream-Yolo



FROM nvcr.io/nvidia/deepstream:6.4-samples-multiarch
COPY --from=yolobuilder /usr/local/lib/libnvdsinfer_yolo_v8.so /usr/local/lib/libnvdsinfer_yolo_v8.so

ARG GL_TOKEN
ARG ENVIRONMENT
ARG MAXINE_VIDEO_SDK
ENV ENVIRONMENT=$ENVIRONMENT
ENV DEBIAN_FRONTEND noninteractive

ENV NVIDIA_DRIVER_CAPABILITIES $NVIDIA_DRIVER_CAPABILITIES,video
ENV LOGLEVEL="INFO"
ENV GST_DEBUG=2


RUN apt update

# GStreamer Dependencies
RUN apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl \
    gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

# # Gst RTSP Server
# RUN apt install -y libgstrtspserver-1.0-dev gstreamer1.0-rtsp

# Deepstream Dependencies
RUN apt install -y python3-gi python3-dev python3-gst-1.0 python-gi-dev git curl python2-dev \
    python3 python3-pip python3-dev cmake g++ build-essential libglib2.0-dev \
    libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev

# Clone the Deepstream Python Apps Repo into <deepstream>/sources
WORKDIR /opt/nvidia/deepstream/deepstream/sources
RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git

# Download and install the Deepstream Python Bindings
RUN mkdir /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings/build
WORKDIR /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings/build


ENV DS_PYTHON_VERION="1.1.10"
RUN curl -O -L https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v${DS_PYTHON_VERION}/pyds-${DS_PYTHON_VERION}-py3-none-linux_x86_64.whl && \
    pip3 install ./pyds-${DS_PYTHON_VERION}-py3-none-linux_x86_64.whl;



# WORKDIR /tmp
# COPY $MAXINE_VIDEO_SDK /tmp/video_fx.tar.gz

# RUN tar -xvf /tmp/video_fx.tar.gz -C /usr/local && \
#     rm -rf /tmp/video_fx.tar.gz

# RUN git clone https://github.com/voidmainvoid95/gst-nvmaxine.git

# RUN cd gst-nvmaxine && \
#     mkdir build && \
#     cd build && \
#     cmake .. && \
#     cmake --build . --config Release && \
#     cmake --install . --config Release && \
#     cd ../../ && \
#     rm -rf gst-nvmaxine

# ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/usr/local/VideoFX/lib"

COPY . /opt/app

WORKDIR /opt/app

RUN pip install -r requirements.txt --extra-index-url https://__token__:$GL_TOKEN@gitlab.com/api/v4/groups/inference/-/packages/pypi/simple

CMD ["/usr/bin/python3", "app.py"]